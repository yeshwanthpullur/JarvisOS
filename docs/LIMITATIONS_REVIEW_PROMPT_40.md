# Prompt 40 Limitations Review

Updated: 2026-08-04

## Method

The review reconciled all 26 open records at commit `4aa197f2bc80001454d8bf0f8d98c22a4271a04c` against implementation, tests, project health, subsystem documents, and the unchanged roadmap order. **Fix Now** required no new service, hardware, credentials, major architecture, safety relaxation, or later milestone work and had to be fully testable locally.

Priority score = user value + MVP impact + safety benefit + reliability benefit + feasibility + testability - risk - dependency cost. LIM-016 scored **23** (4 + 3 + 4 + 4 + 5 + 5 - 2 - 0) and was the only eligible candidate.

## Classification

- **Fix Now:** contained, safe, locally testable work.
- **Next Roadmap Milestone:** belongs directly to Prompt 41.
- **Blocked by external service or cost:** needs external administration, credentials, or spending.
- **Deferred by design:** substantial later work or nonessential current-MVP scope.
- **Intentionally restricted:** a current safety or privacy boundary, not a defect.

No open record was primarily blocked by local hardware after manual STT and vision verification.

## Complete Inventory

Each row captures user and technical impact, safety/privacy impact, dependency or blocker, evidence, target/action, eligibility, and classification reason.

| ID | Subsystem | Category | Impact and safety/privacy risk | Dependency / blocker | Evidence | Target and recommended action | Fix now? / reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIM-014 | Providers | External service/cost | Mock-only live confidence; external prompts may incur cost or disclose data. | Authorized account, credentials, budget. | Cloud mock tests pass. | Cloud Provider Validation; opt-in smoke test. | No; external authorization. |
| LIM-015 | Tools | Deferred | Narrow execution breadth; connectors add permission/privacy risk. | Validated adapters. | Calculator/text tools pass. | Capability milestones; add governed tools only. | No; broad feature work. |
| LIM-016 | Memory | Fix Now, fixed | Manual lifecycle could accumulate stale duplicates; deletion risks data loss. | Existing local repository. | Startup lifecycle tests pass. | Prompt 40; retain non-destructive policy. | Yes; bounded and testable. |
| LIM-017 | Deployment | External service/cost | Dashboard clutter; automated deletion is unsafe. | Vercel owner dashboard. | Canonical project is Ready. | Manual administration. | No; external control. |
| LIM-018 | Sync | Deferred | No remote transfer; remote data needs encryption and consent. | Authenticated encrypted infrastructure. | Local queue tests pass. | Prompt 43. | No; major later architecture. |
| LIM-019 | Planning | Restricted | Handoff required; prevents uncontrolled mutation. | Approval and rollback design. | Planning tests pass. | Governed execution milestone. | No; safety boundary. |
| LIM-020 | Agents | Deferred | Limited breadth; expansion increases authority/data access. | Validated specialists. | Coordination tests pass. | Future Agent Expansion. | No; feature work. |
| LIM-025 | Voice | Restricted | Explicit capture is less hands-free but prevents hidden listening. | Wake-word privacy review. | Voice status is explicit-only. | Prompt 48. | No; privacy boundary. |
| LIM-026 | Interface | Deferred | Optional UI may lag; remote exposure adds risk. | Stabilization work. | Loopback tests pass. | Interface Stabilization. | No; broad UX milestone. |
| LIM-027 | Web | Restricted | No interactive actions; block prevents unauthorized submissions/account changes. | Approval, rollback, audit. | Policy tests pass. | Prompt 46. | No; safety boundary. |
| LIM-029 | Creative media | Next milestone | No image workflow; generation needs provenance/privacy controls. | Prompt 41. | No adapter exists. | Prompt 41. | No; would start next milestone. |
| LIM-030 | Creative media | Deferred | No video workflow; avoids destructive edits/uploads. | Prompt 42. | No editor module. | Prompt 42. | No; later milestone. |
| LIM-031 | Sync | Deferred | No trusted cross-device state; transport raises privacy risk. | Prompt 43 transport. | Local queue only. | Prompt 44. | No; dependent milestone. |
| LIM-032 | Hardware | Deferred | No verified profiles; physical actions need safety gates. | Hardware/toolchain access. | No module. | Existing hardware milestone. | No; major hardware scope. |
| LIM-033 | Study | Deferred | No composed workflow; academic attribution needs controls. | Workflow composition. | Components exist separately. | Future Study/Research milestone. | No; major workflow. |
| LIM-034 | Builder | Deferred | No end-to-end authority; uncontrolled composition is risky. | Governed orchestration. | Components exist separately. | Future Builder milestone. | No; major architecture. |
| LIM-035 | Communication | Deferred | No connectors; private communication requires consent. | Connector/approval boundaries. | No connector. | Prompt 47. | No; privacy-sensitive milestone. |
| LIM-036 | Workspace | Deferred | Capabilities remain separate; hidden sharing must be avoided. | Approved composition layer. | Modules are independently available. | Prompt 49. | No; later product milestone. |
| LIM-037 | Mobile | Deferred | No live phone control; private access remains absent. | Trusted adapter/enrollment. | Planning-only tests pass. | Future Mobile Adapter. | No; hardware/architecture. |
| LIM-038 | Mobile | Deferred | No phone actions; block protects messages, sensors, accounts. | Scoped approvals/rollback. | Policy tests pass. | Future Mobile Actions. | No; sensitive-action work. |
| LIM-039 | Mobile | Deferred | No companion endpoint; identifiers/transport need privacy design. | Companion app/enrollment. | No implementation. | Future Mobile Companion. | No; new product surface. |
| LIM-042 | Vision | Deferred | Still images only; live capture raises surveillance risk. | Camera/video safety milestone. | No stream adapter. | Future Camera/Video milestone. | No; hardware/privacy scope. |
| LIM-043 | Vision | Restricted | No identity/sensitive-trait inference; prevents biometric harm. | Permanent policy. | Requests rejected before dispatch. | Permanent Safety Boundary. | No; must remain restricted. |
| LIM-044 | Vision | Deferred | Local-only; cloud upload would expose images. | Cloud privacy review. | Vercel has no image endpoint. | Optional Cloud Vision Review. | No; local-first design. |
| LIM-045 | Vision | Deferred | OCR may be wrong; overconfidence would mislead. | Engine and benchmark corpus. | Verification warning exists. | Future OCR Evaluation. | No; accuracy cannot be proven now. |
| LIM-046 | Vision | Restricted | No medical/legal/forensic certainty; prevents high-stakes misuse. | Permanent human-expert boundary. | Unsafe requests rejected. | Permanent Safety Boundary. | No; must remain restricted. |

## Implementation Result

LIM-016 was caused by lifecycle work being available only through explicit `memory cleanup`. Initialization now runs the same bounded policy when consolidation is enabled. Expired active records become archived, exact active duplicates become superseded, audit metadata stays content-free, and no memory is automatically deleted.

The limitations CLI provides bounded `status`, `open`, `fixed`, `show`, `category`, `next`, and `summary` views. Malformed data fails closed. `project status` includes fixed, open, intentional-restriction, and external-block counts.

## Counts

- Before: 47 total, 21 fixed, 26 open.
- After: 47 total, 22 fixed, 25 open.
- Remaining: 1 next milestone, 2 external service/cost, 17 deferred, 5 intentionally restricted.
- Highest-priority remaining item: LIM-029, owned by Prompt 41.

Roadmap order was not changed. Prompt 41 was not started.
