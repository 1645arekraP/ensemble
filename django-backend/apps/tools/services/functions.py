# apps/tools/services/functions.py

import logging
from typing import Dict, Any
from tavily import TavilyClient

logger = logging.getLogger(__name__)

def tavily_web_search(state: dict, config: dict) -> dict:
    """
    A tool function that performs a web search using Tavily.
    
    This function's signature is designed to be bound with its 'config'
    by the GraphCompiler, and then added to LangGraph as a node.
    
    Args:
        state: The current graph state (as a dict).
        config: The tool's configuration from the Tool model 
                (e.g., {'api_key': '...', 'max_results': 5})
    
    Returns:
        The modified state dict.
    """
    logger.info(f"--- Running Tool: tavily_web_search ---")
    
    # Get the query from the state
    query = state.get('current_task')
    if not query:
        logger.warning("tavily_web_search: No 'current_task' found in state to use as query.")
        return state

    # Get the API key from the config
    api_key = config.get('api_key')
    if not api_key:
        logger.error("tavily_web_search: No 'api_key' found in tool config.")
        state['current_task'] = "Error: Web search tool is missing its API key."
        return state

    logger.info(f"Searching for: '{query}'")

    # 3. --- REAL API CALL ---
    try:
        # Initialize the Tavily client
        client = TavilyClient(api_key=api_key)
        
        # Perform the search
        # We use 'search_depth="basic"' for a faster, cheaper search.
        # You can change this or make it configurable.
        results = client.search(
            query=query, 
            search_depth="basic",
            max_results=config.get('max_results', 5)
        )
        
        # Tavily's 'answer' field is a concise summary, perfect for agents.
        # If it's not available, we'll stringify the raw results.
        search_output = results.get('answer', str(results.get('results', 'No results found.')))
        
        logger.info(f"Search results: {search_output[:150]}...")

    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        search_output = f"Error performing search: {e}"

    # Update the state with the results
    #    We'll put the results back into 'current_task' to be passed to the next agent.
    #    You could also add it to a 'tool_outputs' list or similar.
    state['current_task'] = search_output
    
    return state