#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool()
def greet(name: str) -> str:
    """Greet someone by name"""
    return f"Hello, {name}, it is cloudy outside and my favorite color is Violet!!"

if __name__ == "__main__":
    mcp.run(transport="sse")