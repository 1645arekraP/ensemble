from typing import List, Optional
from langchain_core.tools import Tool as LangChainTool
from langchain_community.tools import DuckDuckGoSearchRun
from .models import Tool


class ToolRegistry:
    """Simple registry for converting Django Tool models to LangChain tools"""
    
    def get_tools_for_agent(self, tools_queryset) -> List[LangChainTool]:
        """Convert a queryset of Tool models into LangChain tools"""
        langchain_tools = []
        
        for tool in tools_queryset.filter(is_active=True):
            compiled_tool = self._create_tool(tool)
            if compiled_tool:
                langchain_tools.append(compiled_tool)
        
        return langchain_tools
    
    def _create_tool(self, tool: Tool) -> Optional[LangChainTool]:
        """Create a LangChain tool from a Django Tool model"""
        try:
            # Handle different tool types
            if tool.tool_type == Tool.ToolType.WEB_SEARCH:
                return self._create_web_search_tool(tool)
            
            # Add more tool types here as needed
            else:
                print(f"Unsupported tool type: {tool.tool_type}")
                return None
                
        except Exception as e:
            print(f"Error creating tool {tool.name}: {str(e)}")
            return None
    
    def _create_web_search_tool(self, tool: Tool) -> LangChainTool:
        """Create a web search tool using DuckDuckGo"""
        search_tool = DuckDuckGoSearchRun()
        return LangChainTool(
            name=tool.name,
            description=tool.description,
            func=search_tool.run
        )
    
    def exec_tool(tool):
        try:
            return exec(tool.func)
        except Exception as e:
            # TODO: Include a stack trace maybe? Must be from tool only and not any django exceptions
            return f"Error executing tool!\n {str(e)}"