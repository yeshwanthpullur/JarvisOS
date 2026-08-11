# Policy Runtime

Policies are versioned and lifecycle-aware: draft, review, approved, active, deprecated, disabled, or archived. Only active policies participate in evaluation.

Precedence is deterministic: security, execution, approval, workflow, runtime, then provider. Duplicate identifiers and ambiguous equal-priority conflicts fail closed. Privileged operations default to denial.

Policy decisions are advisory to existing authorities and always report `execution_authorized=false`.
