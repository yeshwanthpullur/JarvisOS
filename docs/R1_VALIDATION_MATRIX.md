# R1 Validation Matrix

Recorded 2026-09-09. Inputs are synthetic and non-sensitive. Runtime artifacts are in ignored `data/revenue_validation/`.

| Run | Input class | Result | Quality | Failure | Provider | Fallback | Cost | Review |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | simple research | completed review-required | pass | none | synthetic/local | typed evidence | UNKNOWN | required |
| 02 | technical comparison | completed review-required | pass | none | synthetic/local | typed evidence | UNKNOWN | required |
| 03 | engineering topic | completed review-required | pass | none | synthetic/local | typed evidence | UNKNOWN | required |
| 04 | poorly specified request | completed review-required | pass | none | synthetic/local | clarification plan | UNKNOWN | required |
| 05 | missing evidence | degraded | review-required | RESEARCH | synthetic/local | plan-only | UNKNOWN | required |
| 06 | conflicting evidence | completed review-required | pass | none | synthetic/local | bounded evidence | UNKNOWN | required |
| 07 | provider unavailable | degraded | review-required | PROVIDER | unconfigured | local/plan-only | UNKNOWN | required |
| 08 | offline mode | degraded | review-required | PROVIDER | offline | local/plan-only | UNKNOWN | required |
| 09 | repository research | completed review-required | pass | none | synthetic/local | project sources | UNKNOWN | required |
| 10 | quality-gate topic | completed review-required | pass | none | synthetic/local | manual review | UNKNOWN | required |

All runs record start/end timestamps, artifacts, provider state, quality result, review requirement, and measured automated duration. Human minutes and direct costs remain `UNKNOWN` until actually measured.
