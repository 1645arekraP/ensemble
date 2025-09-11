from typing import Dict, Any, Optional, Callable
from langchain_core.tools import Tool as LangChainTool
from langchain_community.tools import DuckDuckGoSearchRun
import importlib
import requests
import json
from .models import Tool


class ToolRegistry:
    """Registry for converting Django Tool models to LangChain tools"""
    
    def __init__(self):
        self._compiled_tools = {}
        self._built_in_tools = self._register_built_in_tools()
    
    def _register_built_in_tools(self) -> Dict[str, Callable]:
        """Register built-in tool implementations"""
        return {
            'web_search': self._create_web_search_tool,
        }
    
    def get_compiled_tool(self, tool: Tool) -> Optional[LangChainTool]:
        """Get a compiled LangChain tool from a Django Tool model"""
        
        if tool.id in self._compiled_tools:
            return self._compiled_tools[tool.id]
        
        if not tool.is_active:
            return None
        
        compiled_tool = self._compile_tool(tool)
        if compiled_tool:
            self._compiled_tools[tool.id] = compiled_tool
        
        return compiled_tool
    
    def _compile_tool(self, tool: Tool) -> Optional[LangChainTool]:
        """Compile a Django Tool into a LangChain tool"""
        
        try:
            # Check for built-in tool implementations
            if tool.name in self._built_in_tools:
                return self._built_in_tools[tool.name](tool)
            
            # Handle custom implementations
            if tool.implementation_module and tool.implementation_class:
                return self._create_custom_tool(tool)
            
            # Handle different tool types
            # TODO: This is where we add our own tool types that langchain doesn't support natively
                
        except Exception as e:
            print(f"Error compiling tool {tool.name}: {str(e)}")
            return None
    
    def _create_web_search_tool(self, tool: Tool) -> LangChainTool:
        """Create a web search tool"""
        search_tool = DuckDuckGoSearchRun()
        return LangChainTool(
            name=tool.name,
            description=tool.description,
            func=search_tool.run
        )
    
    def _create_custom_tool(self, tool: Tool) -> LangChainTool:
        """Create a tool from a custom implementation"""
        try:
            module = importlib.import_module(tool.implementation_module)
            tool_class = getattr(module, tool.implementation_class)
            
            # Instantiate the custom tool
            custom_tool_instance = tool_class(tool.configuration)
            
            return LangChainTool(
                name=tool.name,
                description=tool.description,
                func=custom_tool_instance.execute
            )
        except Exception as e:
            raise Exception(f"Failed to create custom tool: {str(e)}")