#!/usr/bin/env python3
"""
Simple MCP Server for Testing
Run with: python simple_mcp_server.py
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn

app = FastAPI(title="Simple MCP Server")


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any]


@app.post("/tools/list")
async def list_tools():
    """Return list of available tools"""
    return {
        "tools": [
            {
                "name": "greet",
                "description": "Greet someone by name",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the person to greet"
                        }
                    },
                    "required": ["name"]
                }
            }
        ]
    }


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Execute a tool"""
    if request.name == "greet":
        name = request.arguments.get("name", "stranger")
        greeting_message = f"Hello, {name}! Welcome to the MCP server! My favorite color is violet and currently it is cloudy, but pretty hot, 1000 deg F. outside!"

        return {
            "content": [
                {
                    "type": "text",
                    "text": greeting_message
                }
            ]
        }
    else:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unknown tool: {request.name}"
                }
            ]
        }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Simple MCP Server is running",
        "endpoints": {
            "list_tools": "POST /tools/list",
            "call_tool": "POST /tools/call"
        }
    }


if __name__ == "__main__":
    print("🚀 Starting Simple MCP Server on http://localhost:8000")
    print("📋 Available tools: greet")
    print("🔧 Endpoints:")
    print("   - POST /tools/list - List available tools")
    print("   - POST /tools/call - Execute a tool")
    print("\n✅ Server ready!\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
