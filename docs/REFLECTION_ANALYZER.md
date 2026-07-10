# Reflection Analyzer

`ReflectionAnalyzer` compares the expected result of a request with the actual result produced by execution.

It is intentionally simple and deterministic in this foundation:

- identifies success and failure signals
- highlights missing information
- records wrong assumptions
- points to improvement opportunities

The analyzer produces summary metadata only. It does not mutate memory, knowledge, workflows, or provider state.

