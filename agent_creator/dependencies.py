"""Dependency validation helpers for Agent Creator."""

from __future__ import annotations


class DependencyResolver:
    """Validates dependency relationships without loading external systems."""

    def detect_cycle(self, graph: dict[str, tuple[str, ...]]) -> bool:
        """Return whether a dependency graph contains a cycle."""
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for dependency in graph.get(node, ()):
                if visit(dependency):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in graph)

    def missing_dependencies(self, required: tuple[str, ...], available: tuple[str, ...]) -> tuple[str, ...]:
        """Return dependencies not present in the available set."""
        available_set = set(available)
        return tuple(item for item in required if item not in available_set)

