"""Small local MCP server used only by protocol integration tests."""

from mcp.server.fastmcp import FastMCP


server = FastMCP("Jarvis MCP protocol test")


@server.tool(description="Read-only search of deterministic test documentation")
def search_docs(query: str) -> str:
    return f"test-result:{query[:40]}"


@server.resource("test://docs/readme", name="Test README", mime_type="text/plain")
def read_docs() -> str:
    return "MCP protocol fixture content"


@server.prompt(name="summarize_test", description="Deterministic fixture prompt")
def summarize_test() -> str:
    return "Summarize the test fixture."


if __name__ == "__main__":
    server.run(transport="stdio")
