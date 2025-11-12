import json
import logging
from django.conf import settings
from django.db.models import Q 
import google.generativeai as genai 
from apps.agents.models import Agent
from apps.tools.models import Tool
from apps.users.models import User 

logger = logging.getLogger(__name__)

# --- Google client setup ---
try:
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in environment variables.")
    genai.configure(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Google Generative AI: {e}")
# --- End Google client setup ---


def generate_graph_from_prompt(prompt: str, user: User, current_graph_data: dict) -> dict:
    """
    Uses an LLM to generate or *edit* a graph_data JSON structure
    based on a user's prompt, their available nodes, and the current graph state.
    """
    
    # Get available "building blocks" (same as before)
    agents = Agent.objects.filter(Q(user=user) | Q(user__isnull=True))
    tools = Tool.objects.filter(Q(user=user) | Q(user__isnull=True)) 

    # --- Debugging loggers ---
    logger.info(f"--- Graph Generator for User: {user.email} ---")
    logger.info(f"Found {agents.count()} agents:")
    for agent in agents:
        logger.info(f"  - Agent: {agent.name} (User: {agent.user_id or 'Global'})")
        
    logger.info(f"Found {tools.count()} tools:")
    for tool in tools:
        logger.info(f"  - Tool: {tool.name} (User: {tool.user_id or 'Global'})")
    # --- End Debugging ---

    # Format building blocks
    available_agents_str = "\n".join(
        f"- type: 'agent', name: '{agent.name}', description: '{agent.description}', data: {{ \"id\": {agent.id}, \"name\": \"{agent.name}\", \"role\": \"{agent.role}\" }}"
        for agent in agents
    )
    available_tools_str = "\n".join(
        f"- type: 'tool', name: '{tool.name}', description: '{tool.description}', data: {{ \"id\": {tool.id}, \"name\": \"{tool.name}\", \"tool_type\": \"{tool.tool_type}\" }}"
        for tool in tools
    )
    
    # --- CONVERT CURRENT GRAPH TO JSON ---
    current_graph_json = json.dumps(current_graph_data, indent=2)

    # --- UPDATE THE SYSTEM PROMPT ---
    system_prompt = f"""
    You are an intelligent workflow editor. Your task is to generate a valid graph JSON structure for a React Flow canvas based on a user's prompt.
    You will be given the user's "available building blocks" (agents and tools) AND their "current graph" (nodes and edges).
    
    Your goal is to modify the "current graph" based on the user's prompt.
    
    --- IMPORTANT SUPERVISOR RULE ---
    If any agent in the "Available Agents" or "Current Graph" has `"role": "supervisor"`, you MUST build a "hub-and-spoke" graph.
    1. The Supervisor node is the central hub.
    2. Draw edges FROM the Supervisor TO every other node (all other agents and tools).
    3. Draw edges FROM every other node (all other agents and tools) BACK TO the Supervisor.
    4. DO NOT draw edges between non-supervisor nodes (e.g., Agent A -> Agent B is forbidden).
    5. If the user asks to "connect Agent A to Tool B", you must interpret this as "connect Supervisor to Agent A, Agent A to Supervisor, Supervisor to Tool B, and Tool B to Supervisor".

    You must return *ONLY* a valid JSON object with two keys:
    1. "explanation": A short, friendly, one or two-sentence explanation of what you did.
    2. "graph": The *new, complete* JSON object for the graph, containing "nodes" and "edges".

    --- Available Building Blocks ---
    Available Agents:
    {available_agents_str or "No agents available."}

    Available Tools:
    {available_tools_str or "No tools available."}
    
    --- User's Current Graph ---
    {current_graph_json}

    --- Response Format ---
    You must respond with a JSON object like this:

    --- SUPERVISOR Example Response (Use this if a supervisor is present) ---
    {{
      "explanation": "I've set up your 'Gemini' supervisor to coordinate the 'Poet' agent and the 'Captain' agent.",
      "graph": {{
        "nodes": [
          {{
            "id": "node-1",
            "type": "agent",
            "position": {{"x": 400, "y": 100}},
            "data": {{ "id": 4, "name": "Gemini", "role": "supervisor" }}
          }},
          {{
            "id": "node-2",
            "type": "agent",
            "position": {{"x": 100, "y": 300}},
            "data": {{ "id": 6, "name": "Poet", "role": "general" }}
          }},
          {{
            "id": "node-3",
            "type": "agent",
            "position": {{"x": 700, "y": 300}},
            "data": {{ "id": 9, "name": "Captain 'Short-Hand' Scallywag", "role": "general" }}
          }}
        ],
        "edges": [
          {{ "id": "edge-1", "source": "node-1", "target": "node-2" }},
          {{ "id": "edge-2", "source": "node-2", "target": "node-1" }},
          {{ "id": "edge-3", "source": "node-1", "target": "node-3" }},
          {{ "id": "edge-4", "source": "node-3", "target": "node-1" }}
        ]
      }}
    }}

    --- Simple Example Response (Use this if NO supervisor is present) ---
    {{
      "explanation": "I've connected your 'Read Gmail' tool to your 'Summarizer' agent.",
      "graph": {{
        "nodes": [
          {{
            "id": "node-1",
            "type": "tool",
            "position": {{"x": 100, "y": 100}},
            "data": {{ "id": 1, "name": "Read Gmail", "tool_type": "gmail" }}
          }},
          {{
            "id": "node-2",
            "type": "agent",
            "position": {{"x": 300, "y": 200}},
            "data": {{ "id": 5, "name": "Summarizer Agent", "role": "general" }}
          }}
        ],
        "edges": [
          {{ "id": "edge-1", "source": "node-1", "target": "node-2" }}
        ]
      }}
    }}
    """
    
    # --- Logging ---
    logger.info("--- Sending System Prompt to LLM ---")
    logger.info(system_prompt)
    logger.info(f"User Prompt: {prompt}")

    # Call the Google LLM (same as before)
    try:
        generation_config = genai.types.GenerationConfig(response_mime_type="application/json")
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt,
            generation_config=generation_config
        )
        response = model.generate_content(prompt)

        if not response.parts:
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Unknown"
            logger.error(f"Error generating graph from LLM: Blocked - {block_reason}")
            raise Exception(f"Failed to generate graph: The prompt was blocked ({block_reason})")

        response_content = response.text
        logger.info(f"--- LLM Response ---: {response_content}")
        
        generated_json = json.loads(response_content)
        return generated_json

    except Exception as e:
        logger.error(f"Error generating graph from LLM: {e}")
        raise Exception(f"Failed to generate graph: {e}")