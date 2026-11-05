"""Opt-in test provider: buffered Haiku output with shared pacing and seeded faults.

This is application bootstrap, not OS admission or coding recovery policy. Normal
AgentConfig instances and HTTPInference clients do not use this module.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import random
import secrets
import time
from contextlib import suppress
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ..config import AgentConfig
from ..contracts import Wire
from ..primitives import canonical
from ..runtime.inference import (
    HTTPInference,
    IncompleteGeneration,
    ModelResponseError,
    ProviderError,
    UnknownExecution,
    terminal_call,
)
from .system_settings import simulation_config

PREFIX = "simulation/inference/"
VERSION = 1


class SimulationSettings(Wire):
    mode: Literal["normal", "buggy", "slow-buggy"] = "slow-buggy"
    tps: Annotated[float, Field(strict=True, gt=0, le=100000, allow_inf_nan=False)] = 30.0
    batch: Annotated[int, Field(strict=True, ge=1, le=16)] = 2
    bug_rate: Annotated[float, Field(strict=True, ge=0, le=100, allow_inf_nan=False)] = 5.0
    seed: Annotated[int, Field(strict=True, ge=0, le=2**53 - 1)] = Field(default_factory=lambda: secrets.randbits(53))
    prefill_seconds: Annotated[float, Field(ge=0, le=60, allow_inf_nan=False)] = 1.5
    prefill_tps: Annotated[float, Field(gt=0, le=1000000, allow_inf_nan=False)] = 2000.0
    jitter: Annotated[float, Field(ge=0, le=0.5, allow_inf_nan=False)] = 0.2
    stall_rate: Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)] = 5.0
    stall_seconds: Annotated[float, Field(ge=0, le=60, allow_inf_nan=False)] = 3.0
    restart_seconds: Annotated[float, Field(gt=0, le=300, allow_inf_nan=False)] = 15.0


class SimulationAgentConfig(AgentConfig):
    """Only explicitly simulated runs acquire an additional configuration field."""

    inference_simulation: SimulationSettings

    @model_validator(mode="after")
    def simulation_resources(self):
        settings = self.inference_simulation
        if settings.mode == "normal":
            raise ValueError("Normal mode uses ordinary AgentConfig without inference_simulation")
        if self.local.protocol not in {"chat", "responses", "anthropic", "gemini"}:
            raise ValueError("Inference simulation requires a raw HTTP local lane")
        if (self.role_bindings["worker"] != "local" or self.local.max_inflight != settings.batch
                or self.max_workers != settings.batch
                or self.local.reserved_context_tokens < settings.batch * self.local.max_context_tokens):
            raise ValueError("Simulation batch must match worker/slot capacity and full-context reservations")
        return self


def configure_simulation(config, options):
    settings = SimulationSettings.model_validate(options)
    if settings.mode == "normal":
        if isinstance(config, SimulationAgentConfig):
            return AgentConfig.model_validate(config.model_dump(exclude={"inference_simulation"}),
                                              context={"resolve_environment_capacity": False})
        return config
    config = simulation_config(config, settings.batch)
    return SimulationAgentConfig.model_validate(
        {**config.model_dump(), "inference_simulation": settings.model_dump()},
        context={"resolve_environment_capacity": False},
    )


class SharedDecoder:
    """Account virtual output tokens across concurrently decoding requests.

    There is no timer task or storage lock. Callers advance the same monotonic
    clock before changing membership. All active requests share one capacity.
    """

    def __init__(self, tps, clock=time.monotonic):
        self.tps, self.clock = tps, clock
        self.updated = clock()
        self.active = {}

    def advance(self):
        current = self.clock()
        if self.active:
            factor = sum(row["factor"] for row in self.active.values()) / len(self.active)
            share = max(0, current - self.updated) * self.tps * factor / len(self.active)
            for row in self.active.values():
                row["tokens"] += share
        self.updated = current

    def add(self, key, factor):
        self.advance()
        self.active[key] = {"tokens": 0.0, "factor": factor}

    def remove(self, key):
        self.advance()
        self.active.pop(key, None)

    def tokens(self, key):
        self.advance()
        return self.active[key]["tokens"]


class SimulationInterrupted(ModelResponseError):
    """Artificial waiting stopped after a real provider terminal response."""

    retryable = False


class SimulatedHTTPInference(HTTPInference):
    def __init__(self, endpoint, settings, records, artifacts):
        super().__init__(endpoint)
        self.settings, self.records, self.artifacts = settings, records, artifacts
        self.decoder = SharedDecoder(settings.tps)

    def update(self, key, value):
        retained = self.records.get(key)
        self.records.compare_and_publish({key: retained[0] if retained else 0}, {key: value})

    def decision(self, request):
        key = PREFIX + "decision/" + request.operation_id
        existing = self.records.get(key)
        if existing:
            return existing[1]
        seed = hashlib.sha256(canonical([VERSION, self.settings.seed, request.operation_id])).digest()
        rng = random.Random(int.from_bytes(seed, "big"))
        server = self.records.get(PREFIX + "server")
        recovering = server and server[1]["restart_until"] > time.time()
        fault = "restarting" if recovering else None
        incident = False
        if not recovering and rng.random() < self.settings.bug_rate / 100:
            fault = rng.choices(["unavailable", "empty", "malformed", "cutoff", "restart"],
                                weights=[40, 20, 15, 20, 5])[0]
            incident = True
        until = server[1]["restart_until"] if recovering else None
        if fault == "restart":
            until = time.time() + self.settings.restart_seconds
        value = {"version": VERSION, "operation_id": request.operation_id,
                 "fault": fault, "incident_started": incident, "restart_until": until,
                 "speed_factor": rng.uniform(1 - self.settings.jitter, 1 + self.settings.jitter),
                 "stall_seconds": self.settings.stall_seconds
                 if rng.random() < self.settings.stall_rate / 100 else 0}
        # Publish restart state and the immutable decision atomically, before any await.
        if fault == "restart":
            server_key = PREFIX + "server"
            retained = self.records.get(server_key)
            self.records.compare_and_publish(
                {server_key: retained[0] if retained else 0},
                {server_key: {"restart_until": until, "operation_id": request.operation_id}}, {key: value})
        else:
            self.records.put_once(key, value)
        return value

    @staticmethod
    def output_tokens(response):
        usage = response.get("usage") or {}
        value = usage.get("output_tokens", usage.get("completion_tokens"))
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return value, "provider_reported"
        return max(1, math.ceil(len(response.get("text", "").encode()) / 4)), "estimated_utf8_bytes_div_4"

    async def generate_operation(self, request, messages, max_output, *, prepared):
        """The OS supplies identity/deadline; this adapter owns artificial latency.

        The actual HTTP call retains its endpoint timeout. Only artificial waits
        can outlive that timeout, and never the original operation deadline.
        """
        started = time.monotonic()
        decision = self.decision(request)
        key = PREFIX + "attempt/" + request.operation_id
        row = {**decision, "phase": "starting", "submitted": False, "injected": False,
               "process_id": request.scope.process_id, "elapsed_seconds": 0}
        self.update(key, row)
        task, response = None, None
        registered = False
        last_report = -1.0

        def report(phase, *, force=False, **values):
            nonlocal last_report
            elapsed = time.monotonic() - started
            if force or elapsed - last_report >= 1 or row["phase"] != phase:
                row.update(phase=phase, elapsed_seconds=round(elapsed, 3), **values)
                self.update(key, row)
                last_report = elapsed

        def interrupted():
            control = self.records.get("process-control/" + request.scope.process_id)
            return bool(control and control[1].get("cancel_requested"))

        async def pause():
            if task.done() and interrupted():
                raise asyncio.CancelledError("Cancellation requested during simulated generation")
            await asyncio.sleep(0.1)

        try:
            if decision["fault"] in {"unavailable", "restart", "restarting"}:
                row["injected"] = True
                error = ProviderError("Simulated inference server " + decision["fault"],
                                      category="service_unavailable", submitted=False)
                error.diagnostics.update(simulated=True, simulation_decision=PREFIX + "decision/" + request.operation_id)
                raise error
            row["submitted"] = True
            # Deployment transport budget stays separate from synthetic pacing.
            task = asyncio.create_task(terminal_call(
                super().generate(messages, max_output, prepared=prepared),
                self.endpoint.lifecycle.total_seconds if self.endpoint.lifecycle else self.endpoint.timeout_seconds))
            if self.settings.mode == "slow-buggy":
                prompt_tokens = math.ceil(sum(len(message["content"].encode()) for message in messages) / 4)
                prefill = self.settings.prefill_seconds + prompt_tokens / self.settings.prefill_tps
                report("prefill", force=True, estimated_prompt_tokens=prompt_tokens)
                while time.monotonic() - started < prefill:
                    if task.done():
                        task.result()  # Preserve real provider failures promptly.
                    await pause()
                stall_end = time.monotonic() + decision["stall_seconds"]
                while time.monotonic() < stall_end:
                    report("stalled")
                    if task.done():
                        task.result()
                    await pause()
                self.decoder.add(request.operation_id, decision["speed_factor"])
                registered = True
            report("provider")
            while not task.done():
                report("provider")
                await pause()
            response = task.result()
            # Real terminal evidence survives interruption during artificial waiting.
            receipt = self.artifacts.put(canonical(response), request.scope)
            self.records.put_once(PREFIX + "provider/" + request.operation_id,
                                  {"response_ref": receipt.model_dump(mode="json"), "confirmed_stopped": True})
            tokens, provenance = self.output_tokens(response)
            if registered:
                while self.decoder.tokens(request.operation_id) < tokens:
                    report("decoding", output_tokens=tokens, token_provenance=provenance,
                           simulated_tokens=round(self.decoder.tokens(request.operation_id), 1))
                    await pause()
            if interrupted():
                raise asyncio.CancelledError("Cancellation requested during simulated generation")
            fault = decision["fault"]
            if fault == "cutoff":
                row["injected"] = True
                partial = {**response, "text": response["text"][:max(1, len(response["text"]) // 2)]}
                error = IncompleteGeneration(partial, "simulated_output_cutoff", max_output)
                error.diagnostics["simulated"] = True
                raise error
            if fault in {"empty", "malformed"}:
                row["injected"] = True
                raise ModelResponseError("Simulated " + fault + " model response",
                    {**response, "text": "" if fault == "empty" else "{simulated invalid response"},
                    {"category": "model_output", "reason": fault, "submitted": True, "simulated": True})
            report("completed", force=True, output_tokens=tokens, token_provenance=provenance,
                   simulated_tokens=tokens)
            return response
        except asyncio.CancelledError as exc:
            if response is None and task and task.done() and not task.cancelled():
                try:
                    response = task.result()
                except (ProviderError, IncompleteGeneration, ModelResponseError) as terminal:
                    report("failed", force=True)
                    raise terminal from exc
                except Exception:
                    pass  # A lost/unknown provider outcome remains uncertain below.
            if response is not None:
                report("interrupted", force=True)
                raise SimulationInterrupted("Simulated waiting interrupted after provider completion", response,
                    {"category": "simulation_interrupted", "submitted": True, "simulated": True}) from exc
            report("uncertain", force=True)
            raise UnknownExecution("Provider execution interrupted before a terminal response") from exc
        except BaseException as exc:
            report("uncertain" if isinstance(exc, (UnknownExecution, asyncio.TimeoutError)) else "failed", force=True)
            raise
        finally:
            if registered:
                self.decoder.remove(request.operation_id)
            if task and not task.done():
                task.cancel()
                with suppress(BaseException):
                    await task


async def install_simulation(runtime, settings):
    """Trusted application bootstrap; never invoked for normal configurations."""
    runtime.records.put_once(PREFIX + "config", {"version": VERSION, **settings.model_dump()})
    original = runtime.clients["local"]
    client = SimulatedHTTPInference(runtime.config.local, settings, runtime.records, runtime.artifacts)
    client.output_cap = original.output_cap
    client.require_completion_metadata = original.require_completion_metadata
    await original.close()
    runtime.clients["local"] = client


def simulation_view(records, configuration):
    settings = configuration.get("inference_simulation")
    if not settings:
        return None
    attempts = [value for key, value in records.items() if key.startswith(PREFIX + "attempt/")]
    return {"settings": settings, "incidents": sum(row["incident_started"] and row["injected"] for row in attempts),
            "affected_attempts": sum(row["injected"] for row in attempts),
            "attempts": attempts, "server": records.get(PREFIX + "server")}
