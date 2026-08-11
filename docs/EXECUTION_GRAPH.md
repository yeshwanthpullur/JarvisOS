# Execution Graph

Agent tasks form a directed acyclic graph with hard, soft, optional, parallel, and fallback dependencies. Cycles, self-dependencies, unknown dependencies, empty graphs, and oversized graphs fail closed. Hard failures block dependents; soft/optional failures may produce bounded partial results. Approval, Broker, execution, and verification ordering is never parallelized or reordered.

The graph also preserves the earlier workflow concepts: directed, sequential, parallel, conditional, and nested paths with validation and optimization metadata. Prompt 81 makes bounded agent-task DAG scheduling available while workflow execution remains owned by its existing subsystem.

Supported workflow graph concepts:
- directed graph
- sequential paths
- parallel paths
- conditional paths
- nested paths
- validation
- optimization
- future DAG execution
