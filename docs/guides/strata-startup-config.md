# Synchronize Strata startup configuration

The coding application can synchronize an existing Strata launch JSON. Configure
top-level local_strata_config with that file's path, relative to the agent config,
or supply --strata-config to this no-inference preparation command:

```bash
polyinference configure-local agent.json --strata-config strata.json
```

It derives Strata's --max-context from the same pair, preserves unrelated serving
settings, and retains the original file as strata.json.before-polyinference.
Both --max-context VALUE and --max-context=VALUE are supported; duplicate or
invalid context arguments reject without changing the launch file.
Restart Strata using that launch file, then start the fresh PolyInference run.
When local_strata_config is configured, run startup repeats synchronization and
stops before model calls if the launch configuration changed and needs a restart.
configure-local and run synchronization do not signal, reload or launch the server.
For automatic startup when opening the UI, separately set agent local_strata_profile
to a saved profile name; see UI launch lifecycle (`docs/guides/launching.md`). Tokenizer/model
capacity and GPU scheduling remain provider-owned. Raw requests carry the pair's
output cap directly, including Claude stand-ins.
