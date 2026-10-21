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
| Provider/retry pause audit | [Pause/retry audit](pause-retry-audit-2026-10-20.md) |
| Input/output cap inventory | [Safeguards audit](inference-cap-safeguards-audit-2026-10-20.md) |
| Completed I/O/settings/handoff checks | [Verification report](io-safety-verification-2026-10-20.md) |
| Canonical memory and optional context | [Implementation report](memory-implementation-report-2026-10-20.md) |
| Memory pressure in retained runs | [Records audit](memory-records-audit-2026-10-20.md), [measurements](memory-records-audit-2026-10-20.json) |
| Generated outputs/native authority | [Boundary investigation](workspace-output-and-native-boundary.md) |

After implementing a resulting fix, update affected module/design/usage docs,
the current issue status and [FIXES.md](FIXES.md). Preserve original evidence and
state what new verification covers the previously missed trigger.
