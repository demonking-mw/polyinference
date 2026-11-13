# Test or warm up an endpoint

Expand Endpoint testing in the UI, select timings, then click Test endpoint / warm
up. It submits one ordinary query under the configured local token pair, with no tools/Git/workspace or
retries. Opening the page never warms a model. Probes and their journals live
under .polyinference/ui/probes/; a pending/uncertain probe blocks another launch
or probe in that manager. Use the saved generic RuntimeConfig with KernelRuntime.reconcile_stopped and
actual termination evidence before further work; the UI observes settled records.
Restarting the UI does not clear this guard. This
is bring-up tooling, not a shared admission service across independent OS runs.
Probe placement stays unspecified unless declared by the endpoint. Run-wide data
policy remains mandatory; a local lane or URL cannot attest a constrained location.

Inspect inference-progress/<operation> for last output, elapsed time and deadline;
model-retry/<root>/<attempt> records source (native/caller), and retry outcomes
record both counters. effect records retain transport cause/stage, physical
uncertainty and discarded delivery. Save run preserves them; snapshots stay read-only.

Offline tests use deterministic parser fixtures, mock transports, bounded timing
faults and real loopback SSE fixtures. The optional TPS simulator still paces
completed real responses; it does not emulate a provider's streaming decoder or
prove GPU scheduling. Real provider/cold-start tests require a separate explicit
live run. See [fixture coverage](../../tests/test_inference_lifecycle.py).
