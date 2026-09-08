# R1 Failure Analysis

Synthetic validation on 2026-09-08 executed ten cases.

| Class | Count | Finding | Action |
| --- | ---: | --- | --- |
| RESEARCH | 1 | No evidence retrieved | Keep degraded and require approved evidence. |
| PROVIDER | 2 | Provider unconfigured/offline | Keep local fallback and report unavailable. |
| INPUT | 0 | No unrecoverable input failure | Continue bounded schema validation. |
| VERIFICATION | 0 | No verifier defect observed | Preserve provenance gate. |
| SYNTHESIS | 0 | No synthesis defect observed | Keep bounded output. |
| DOCUMENT | 0 | Artifact creation passed | Preserve isolated outputs. |
| QUALITY | 0 | No unexpected quality failure | Keep human review required. |
| TOOL | 0 | No tool side effect | Keep plan-only boundary. |
| RECOVERY | 0 | No recovery failure | Re-run failed cases only in isolated workspaces. |
| HUMAN REVIEW | 10 | Required for every run | No client-ready status is automatic. |

The three degraded cases are intentional policy outcomes, not hidden successes.
