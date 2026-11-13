# Set cloud agent endpoint timeouts

`system.cloud_agent_timeout_interrupt` is a strict boolean, default **false**,
defined in [os_config.py](../../src/polyinference/os_config.py) and exposed to
AgentConfig through the same `system` block. The coding UI uses 1800 seconds
and inherits false without an application override. For cloud AgentJob calls, false makes
`endpoint.timeout_seconds` a one-time warning threshold: the same job, connection,
callbacks, admission slot and accounting continue. It logs a Python WARNING and a
durable `runtime/warning/cloud-agent-timeout/<operation_id>` record without
pausing, retrying or interrupting the run. Set it to **true** to enforce the endpoint
timeout and retain the existing uncertain-execution handling. Direct Codex stdio
read timeouts and proxy HTTP timeouts follow this policy. Physical endpoint
location, rather than lane name, selects cloud jobs. Raw ModelQuery and local-agent
timeouts are unchanged. Original process/root deadlines and explicit cancellation
still apply. Use fresh state for this changed configuration; historical runs are
not silently opted in.
