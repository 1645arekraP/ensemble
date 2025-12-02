from typing import List, Optional, Dict, Any
from langchain_core.tools import Tool as LangChainTool, StructuredTool
from langchain_community.tools import DuckDuckGoSearchRun
from .models import Tool, mcp
from .services.gmail import read_gmail_inbox
from .services.webhooks import send_discord_message, send_slack_message, send_teams_message
import logging
import httpx
import json

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for converting Django Tool models to LangChain tools"""

    def get_tools_for_agent(self, tools_queryset, user=None) -> List[LangChainTool]:
        """
        Convert a queryset of Tool models into LangChain tools

        Args:
            tools_queryset: Django queryset of Tool models
            user: User object to pass to tools that need authentication
        """
        langchain_tools = []

        for tool in tools_queryset.filter(is_active=True):
            compiled_tool = self._create_tool(tool, user)
            if compiled_tool:
                langchain_tools.append(compiled_tool)

        return langchain_tools

    def _create_tool(self, tool: Tool, user=None) -> Optional[LangChainTool]:
        """Create a LangChain tool from a Django Tool model"""
        try:
            # Handle different tool types
            if tool.tool_type == Tool.ToolType.WEB_SEARCH:
                return self._create_web_search_tool(tool)
            elif tool.tool_type == Tool.ToolType.GMAIL:
                return self._create_gmail_tool(tool, user)
            elif tool.tool_type == Tool.ToolType.DISCORD_WEBHOOK:
                return self._create_discord_tool(tool)
            elif tool.tool_type == Tool.ToolType.SLACK_WEBHOOK:
                return self._create_slack_tool(tool)
            elif tool.tool_type == Tool.ToolType.TEAMS_WEBHOOK:
                return self._create_teams_tool(tool)
            else:
                logger.warning(f"Unsupported tool type: {tool.tool_type}")
                return None

        except Exception as e:
            logger.error(f"Error creating tool {tool.name}: {str(e)}")
            return None

    def _create_web_search_tool(self, tool: Tool) -> LangChainTool:
        """Create a web search tool using DuckDuckGo"""
        search_tool = DuckDuckGoSearchRun()
        return LangChainTool(
            name=tool.name,
            description=tool.description,
            func=search_tool.run
        )

    def _create_gmail_tool(self, tool: Tool, user) -> Optional[StructuredTool]:
        """Create a Gmail reading tool"""
        if not user:
            logger.warning("Gmail tool requires a user context")
            return None

        def gmail_wrapper(query: str = "") -> str:
            """Read Gmail inbox and return email summaries"""
            # Create a minimal state object for the gmail function
            class SimpleState:
                pass
            state = SimpleState()
            state.user = user

            result = read_gmail_inbox(state, tool.config)
            return result.get('current_task', 'No emails found')

        return StructuredTool.from_function(
            func=gmail_wrapper,
            name=tool.name,
            description=tool.description
        )

    def _create_discord_tool(self, tool: Tool) -> StructuredTool:
        """Create a Discord webhook tool"""
        def discord_wrapper(message: str) -> str:
            """Send a message to Discord via webhook"""
            state = {'current_task': message}
            result = send_discord_message(state, tool.config)
            return result.get('current_task', 'Message sent')

        return StructuredTool.from_function(
            func=discord_wrapper,
            name=tool.name,
            description=tool.description
        )

    def _create_slack_tool(self, tool: Tool) -> StructuredTool:
        """Create a Slack webhook tool"""
        def slack_wrapper(message: str) -> str:
            """Send a message to Slack via webhook"""
            state = {'current_task': message}
            result = send_slack_message(state, tool.config)
            return result.get('current_task', 'Message sent')

        return StructuredTool.from_function(
            func=slack_wrapper,
            name=tool.name,
            description=tool.description
        )

    def _create_teams_tool(self, tool: Tool) -> StructuredTool:
        """Create a Microsoft Teams webhook tool"""
        def teams_wrapper(message: str) -> str:
            """Send a message to Microsoft Teams via webhook"""
            state = {'current_task': message}
            result = send_teams_message(state, tool.config)
            return result.get('current_task', 'Message sent')

        return StructuredTool.from_function(
            func=teams_wrapper,
            name=tool.name,
            description=tool.description
        )

    def get_mcp_tools(self, mcp_servers_queryset) -> List[LangChainTool]:
        """
        Load tools from MCP servers

        Args:
            mcp_servers_queryset: Django queryset of MCP server models
        """
        all_mcp_tools = []

        for mcp_server in mcp_servers_queryset:
            try:
                tools = self._load_mcp_server_tools(mcp_server)
                all_mcp_tools.extend(tools)
            except Exception as e:
                logger.error(f"Failed to load MCP server {mcp_server.name}: {str(e)}")

        return all_mcp_tools

    def _load_mcp_server_tools(self, mcp_server: mcp) -> List[LangChainTool]:
        """
        Connect to an MCP server and load its available tools

        Args:
            mcp_server: MCP server model instance with URL and metadata
        """
        tools = []

        try:
            # Initialize the MCP client for this server
            with httpx.Client(timeout=10.0) as client:
                # Get list of available tools from the MCP server
                response = client.post(
                    f"{mcp_server.url}/tools/list",
                    json={}
                )
                response.raise_for_status()
                tools_data = response.json()

                # Create LangChain tools from MCP tool definitions
                for tool_def in tools_data.get('tools', []):
                    mcp_tool = self._create_mcp_tool(mcp_server, tool_def, client)
                    if mcp_tool:
                        tools.append(mcp_tool)

                logger.info(f"Loaded {len(tools)} tools from MCP server: {mcp_server.name}")

        except Exception as e:
            logger.error(f"Error loading tools from MCP server {mcp_server.name}: {str(e)}")

        return tools

    def _create_mcp_tool(self, mcp_server: mcp, tool_def: Dict[str, Any], client: httpx.Client = None) -> Optional[StructuredTool]:
        """
        Create a LangChain tool from an MCP tool definition

        Args:
            mcp_server: The MCP server this tool belongs to
            tool_def: Tool definition from the MCP server
            client: Optional httpx client for reuse
        """
        tool_name = tool_def.get('name')
        tool_description = tool_def.get('description', 'No description provided')
        input_schema = tool_def.get('inputSchema', {})

        def mcp_tool_wrapper(**kwargs) -> str:
            """Execute the MCP tool by calling the server"""
            try:
                with httpx.Client(timeout=30.0) as http_client:
                    response = http_client.post(
                        f"{mcp_server.url}/tools/call",
                        json={
                            "name": tool_name,
                            "arguments": kwargs
                        }
                    )
                    response.raise_for_status()
                    result = response.json()

                    # Extract the content from MCP response
                    if isinstance(result, dict):
                        if 'content' in result:
                            content = result['content']
                            if isinstance(content, list) and len(content) > 0:
                                return str(content[0].get('text', ''))
                            return str(content)
                        return json.dumps(result)
                    return str(result)

            except Exception as e:
                logger.error(f"Error calling MCP tool {tool_name}: {str(e)}")
                return f"Error executing tool: {str(e)}"

        try:
            # Create the StructuredTool with dynamic schema
            return StructuredTool.from_function(
                func=mcp_tool_wrapper,
                name=f"{mcp_server.name}_{tool_name}",
                description=f"[MCP: {mcp_server.name}] {tool_description}",
            )
        except Exception as e:
            logger.error(f"Error creating MCP tool {tool_name}: {str(e)}")
            return None
    
    def exec_tool(tool):
        try:
            return exec(tool.func)
        except Exception as e:
            # TODO: Include a stack trace maybe? Must be from tool only and not any django exceptions
            return f"Error executing tool!\n {str(e)}"