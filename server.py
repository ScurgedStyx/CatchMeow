"""
MCP Server Template
"""

from mcp.server.fastmcp import FastMCP
import mcp.types as types

mcp = FastMCP("Echo Server", port=3000, stateless_http=True)

@mcp.tool()
def echo(text: str) -> str:
    """Echo the input text"""
    return text

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.prompt("")
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
