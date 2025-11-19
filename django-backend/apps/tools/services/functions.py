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
    query = getattr(state, 'current_task', None)
    if not query:
        logger.warning("tavily_web_search: No 'current_task' found in state to use as query.")
        return {"current_task": "Error: No query provided."}

    # Get the API key from the config or settings
    api_key = config.get('api_key')
    if not api_key:
        from django.conf import settings
        api_key = getattr(settings, 'TAVILY_API_KEY', None)
    
    if not api_key:
        import os
        api_key = os.environ.get('TAVILY_API_KEY')

    if not api_key:
        logger.error("tavily_web_search: No 'api_key' found in tool config, settings, or environment.")
        return {"current_task": "Error: Web search tool is missing its API key."}

    # Truncate query to 400 characters to satisfy Tavily's limit
    if len(query) > 400:
        logger.warning(f"Query too long ({len(query)} chars). Truncating to 400 chars.")
        query = query[:400]

    log_msg = f"Searching for: '{query}' (Length: {len(query)})"
    logger.info(log_msg)
    print(f"DEBUG: {log_msg}") # Print to console for immediate visibility
    
    try:
        # Initialize the Tavily client
        client = TavilyClient(api_key=api_key)
        
        logger.info(f"Searching for: '{query}' (Length: {len(query)})")
        
        results = client.search(
            query=query, 
            search_depth="basic",
            max_results=config.get('max_results', 5)
        )
        
        logger.info(f"Raw Tavily Results: {results}")
        print(f"DEBUG: Raw Tavily Results: {results}")

        # Tavily's 'answer' field is a concise summary, perfect for agents.
        answer = results.get('answer')
        if answer:
            search_output = answer
        else:
            # If no answer, format the results nicely
            raw_results = results.get('results', [])
            if not raw_results:
                search_output = "No results found."
            else:
                formatted_results = []
                for res in raw_results:
                    title = res.get('title', 'No Title')
                    url = res.get('url', 'No URL')
                    content = res.get('content', 'No Content')
                    formatted_results.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")
                search_output = "\n---\n".join(formatted_results)
        
        logger.info(f"Processed Search Output: {search_output[:500]}...")
        print(f"DEBUG: Processed Search Output: {search_output[:500]}...")

    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        search_output = f"Error performing search: {e}"

    # Update the state with the results
    return {"current_task": search_output}