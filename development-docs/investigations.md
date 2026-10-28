# Investigations and verification evidence

[Development records](README.md) · [Fix history](FIXES.md)

These reports separate observed facts, inference, proposed changes and checks
actually run. Their historical counts are not current verification.

| Topic | Report / evidence |
| --- | --- |
| Initial Minecraft incident | [8e83ed155ae2](run-analysis-8e83ed155ae2.md) |
| Empty completed response | [d434799ad8e4](run-d434799ad8e4-analysis.md) |
| Serialized input overflow | [2de3d5c5ab9b](run-2de3d5c5ab9b-analysis.md) |
| Native inventory interruption | [eb66fc618354](run-eb66fc618354-analysis.md) |
| First two-slot run | [a1859f8644a5](run-a1859f8644a5-analysis.md), [measurements](run-a1859f8644a5-evidence.json) |
| Haiku timeout boundary and foundation test grants | [7086c575ef94](run-7086c575ef94-analysis.md) |
| Provider/retry pause audit | [Pause/retry audit](pause-retry-audit-2026-10-20.md) |
| Input/output cap inventory | [Safeguards audit](inference-cap-safeguards-audit-2026-10-20.md) |
| Completed I/O/settings/handoff checks | [Verification report](io-safety-verification-2026-10-20.md) |
| Canonical memory and optional context | [Implementation report](memory-implementation-report-2026-10-20.md) |
| Memory pressure in retained runs | [Records audit](memory-records-audit-2026-10-20.md), [measurements](memory-records-audit-2026-10-20.json) |
| Generated outputs/native authority | [Boundary investigation](workspace-output-and-native-boundary.md) |
| Reliability merge conflicts and verification | [26 October integration audit](branch-integration-audit-2026-10-26.md) |
| Real local model, recovery and failed product checks | [26 October Strata test](local-strata-live-test-2026-10-26.md) |
| Documentation compliance and cross-run trends | [27 October review](documentation-and-reliability-audit-2026-10-27.md) |
| Detailed OS/agent implementation proposals and past-failure coverage | [27 October reliability plan](run-reliability-implementation-plan-2026-10-27.md) — report only |

After implementing a resulting fix, update affected module/design/usage docs,
the current issue status and [FIXES.md](FIXES.md). Preserve original evidence and
state what new verification covers the previously missed trigger.
