"""Template loader for built-in and future plugin templates."""

from __future__ import annotations

from agent_creator.template_engine import BaseTemplate


class TemplateLoader:
    """Discovers template metadata without filesystem watchers."""

    def __init__(self) -> None:
        self.initialized = True

    def default_template(self) -> BaseTemplate:
        """Return the deterministic built-in agent template."""
        return BaseTemplate(
            template_id="core_agent",
            name="Core Agent Template",
            description="Base template for generated JARVIS OS agents.",
            files={
                "__init__.py": '"""Generated agent package."""\n\nfrom .agent import ${class_name}\n\n__all__ = ["${class_name}"]\n',
                "agent.py": (
                    '"""Generated ${name} agent."""\n\n'
                    "from __future__ import annotations\n\n"
                    "from agents import BaseAgent\n\n\n"
                    "class ${class_name}(BaseAgent):\n"
                    '    """Generated agent shell. No AI or automation is implemented."""\n'
                    "    pass\n"
                ),
                "manifest.json": "${manifest_json}\n",
                "README.md": "# ${name}\n\n${description}\n\nGenerated from `${blueprint_id}` using `${template_id}`.\n",
                "tests.py": (
                    '"""Generated tests for ${name}."""\n\n'
                    "from agents import BaseAgent\n"
                    "from .agent import ${class_name}\n\n\n"
                    "def test_generated_agent_inherits_base_agent():\n"
                    "    assert issubclass(${class_name}, BaseAgent)\n"
                ),
            },
        )

    def discover(self) -> tuple[BaseTemplate, ...]:
        """Return built-in templates."""
        return (self.default_template(),)

