import functools
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel # <-- Import BaseModel

from django.conf import settings
from django.db.models import Q
from langgraph.graph import END, StateGraph
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. Import from the compiler file ---
from ...agents.services.compiler import (
    AgentCompiler, AgentState, SupervisorPromptBuilder, _hydrate_messages
)
from ..models import Graph
from ...agents.models import Agent
from ...executions.models import ExecutionLog, ExecutionStep
from ...tools.models import Tool
from ...tools.services.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

class GraphCompiler:
    """
    Compiles a Graph model into an executable LangGraph
    by using the JSON data in the 'graph_data' field as the source of truth.
    """
    
    def __init__(self, max_executions=15):
        self.agent_compiler = AgentCompiler()
        self.max_executions = max_executions
    
    def compile_graph(self, graph: Graph) -> StateGraph:
        """Compile a Graph model into an executable LangGraph"""
        
        workflow = StateGraph(AgentState)
        
        if 'nodes' not in graph.graph_data or not graph.graph_data['nodes']:
            raise ValueError("Graph data is empty or missing 'nodes' key.")

        nodes_json = graph.graph_data.get('nodes', [])
        edges_json = graph.graph_data.get('edges', [])
        rf_id_to_agent_name_map = {}
        
        available_agent_nodes_for_prompt = []
        available_tool_nodes_for_prompt = []
        
        workflow.add_node("END", lambda state: state)
        supervisor_rf_id = None
        supervisor_name = None
        supervisor_agent = None

        for node in nodes_json:
            node_type = node.get('type', 'agent')
            node_data = node.get('data', {})
            node_name = node_data.get('label') or node_data.get('name')
            rf_id = node.get('id')
            
            if not node_name or not rf_id:
                raise ValueError(f"Node {rf_id} is missing 'id' or 'label'/'name'.")

            rf_id_to_agent_name_map[rf_id] = node_name
            
            if node_type == 'agent':
                agent_db_id = node_data.get('id')
                agent_role = node_data.get('role', 'general')
                if not agent_db_id:
                    raise ValueError(f"Agent node {node_name} missing 'id'.")
                try:
                    agent = Agent.objects.get(id=agent_db_id)
                    if agent_role == 'supervisor':
                        supervisor_rf_id = rf_id
                        supervisor_name = node_name
                        supervisor_agent = agent
                    else:
                        available_agent_nodes_for_prompt.append(agent)
                        # Don't compile yet, will do later
                except Agent.DoesNotExist:
                    raise ValueError(f"Agent '{node_name}' not in database.")

            elif node_type == 'tool':
                tool_db_id = node_data.get('id')
                if not tool_db_id:
                    raise ValueError(f"Tool node {node_name} missing 'id'.")
                try:
                    tool = Tool.objects.get(id=tool_db_id)
                    available_tool_nodes_for_prompt.append(tool)
                    
                    base_tool_function = TOOL_REGISTRY.get(tool.tool_type)
                    if not base_tool_function:
                        raise ValueError(f"Tool type '{tool.tool_type}' not in TOOL_REGISTRY.")
                    
                    tool_config = tool.config or {}
                    
                    # Inject API key from settings if not present in config
                    if tool.tool_type == Tool.ToolType.WEB_SEARCH and 'api_key' not in tool_config:
                        api_key = getattr(settings, 'TAVILY_API_KEY', None)
                        if not api_key:
                            import os
                            api_key = os.environ.get('TAVILY_API_KEY')
                        
                        if api_key:
                            tool_config['api_key'] = api_key
                        else:
                            print(f"WARNING: TAVILY_API_KEY not found in settings or environment for tool {tool.name}")
                    
                    # --- Create a wrapper for the tool node ---
                    def make_tool_node(func, cfg, tool_name):
                        def tool_node_wrapper(state: AgentState) -> AgentState:
                            print("\n" + "🛠️"*40)
                            print(f"🛠️ TOOL EXECUTION: {tool_name}")
                            print("🛠️"*40)
                            try:
                                # Call the tool function with state and config
                                return func(state, config=cfg)
                            except Exception as e:
                                logger.error(f"❌ Tool '{tool_name}' execution failed: {e}")
                                error_msg = AIMessage(content=f"Tool error: {str(e)}")
                                
                                # Return a valid state with the error
                                new_state_dict = state.model_dump()
                                new_state_dict['messages'] = state.messages + [error_msg]
                                return AgentState(**new_state_dict)
                        return tool_node_wrapper
                    
                    tool_node = make_tool_node(base_tool_function, tool_config, node_name)
                    workflow.add_node(node_name, tool_node)

                except Tool.DoesNotExist:
                    raise ValueError(f"Tool '{node_name}' not in database.")

        # --- Compile all agents with full context ---
        graph_context = {
            'graph': graph,
            'available_agents': available_agent_nodes_for_prompt,
            'available_tools': available_tool_nodes_for_prompt
        }
        
        # Compile worker agents
        for agent in available_agent_nodes_for_prompt:
            agent_node = self.agent_compiler.compile_agent(
                agent, 
                graph_context=graph_context,
                max_executions=self.max_executions
            )
            workflow.add_node(agent.name, agent_node)
        
        # Compile supervisor
        if supervisor_name and supervisor_agent:
            supervisor_node = self.agent_compiler.compile_agent(
                supervisor_agent, 
                graph_context=graph_context,
                max_executions=self.max_executions
            )
            workflow.add_node(supervisor_name, supervisor_node)
        
        nodes_with_outgoing_edges = set()
        
        if supervisor_name:
            # --- SUPERVISOR LOGIC ---
            routing_map = {"END": "END", "FINISH": "END"}
            all_node_names_in_graph = set()
            
            for edge in edges_json:
                if edge.get('source') == supervisor_rf_id:
                    target_name = rf_id_to_agent_name_map.get(edge.get('target'))
                    if target_name:
                        routing_map[target_name] = target_name
                        all_node_names_in_graph.add(target_name)
                        nodes_with_outgoing_edges.add(supervisor_rf_id)
            
            def supervisor_router(state: AgentState) -> str:
                """Reads the supervisor's decision from the state and routes."""
                print("\n" + "🔀"*40)
                print("GRAPH ROUTER CALLED")
                print("🔀"*40)
                
                # Handle state being a dict or Pydantic model
                if isinstance(state, dict):
                    decision = state.get('supervisor_decision')
                else:
                    decision = state.supervisor_decision
                
                if not decision:
                    print("⚠️ No supervisor_decision in state! Defaulting to END.")
                    return "END"
                
                next_node = decision.get('next_agent')
                is_complete = decision.get('is_complete', False)
                
                if is_complete or next_node == "FINISH":
                    print("✅ ROUTING DECISION: END (task complete)")
                    return "END"
                
                if next_node and next_node in routing_map:
                    print(f"✅ ROUTING DECISION: {next_node}")
                    return next_node
                
                print(f"⚠️ Decision '{next_node}' not in routing_map! Defaulting to END.")
                return "END"

            workflow.add_conditional_edges(
                supervisor_name,
                supervisor_router,
                routing_map
            )

            for node_name in all_node_names_in_graph:
                workflow.add_edge(node_name, supervisor_name)
                
                rf_id = next((rf_id for rf_id, name in rf_id_to_agent_name_map.items() 
                              if name == node_name), None)
                if rf_id:
                    nodes_with_outgoing_edges.add(rf_id)
        
        else:
            # --- SEQUENTIAL (NON-SUPERVISOR) LOGIC ---
            for edge in edges_json:
                source_agent_name = rf_id_to_agent_name_map.get(edge.get('source'))
                target_agent_name = rf_id_to_agent_name_map.get(edge.get('target'))
                if source_agent_name and target_agent_name:
                    workflow.add_edge(source_agent_name, target_agent_name)
                    nodes_with_outgoing_edges.add(edge.get('source'))

        # 4. Set Entry Point
        if supervisor_name:
            workflow.set_entry_point(supervisor_name)
        else:
            nodes_with_incoming_edges = set(e.get('target') for e in edges_json)
            entry_node = next((n for n in nodes_json if n.get('id') not in nodes_with_incoming_edges), None)
            
            if not entry_node:
                if not nodes_json:
                    raise ValueError("Cannot determine entry point: Graph has no nodes.")
                entry_node = nodes_json[0]
                
            entry_point_name = rf_id_to_agent_name_map[entry_node.get('id')]
            workflow.set_entry_point(entry_point_name)
            
        # 5. Connect Leaf Nodes to END
        if not supervisor_name:
            for node in nodes_json:
                if node.get('id') not in nodes_with_outgoing_edges:
                    agent_name = rf_id_to_agent_name_map[node.get('id')]
                    workflow.add_edge(agent_name, "END")

        return workflow.compile()

# --- Graph Runner ---

class GraphRunner:
    """Executes compiled graphs and manages execution state"""
    
    def __init__(self, max_executions=15):
        self.graph_compiler = GraphCompiler(max_executions=max_executions)
        self.active_executions = {}
        self.max_executions = max_executions
    
    def run_graph(self, graph: Graph, initial_input: str, context: Dict = None, user=None) -> Dict[str, Any]:
        
        execution_log = None
        if user:
            execution_log = ExecutionLog.objects.create(
                graph=graph,
                user=user,
                initial_input=initial_input,
                context=context or {}
            )
        
        try:
            compiled_graph = self.graph_compiler.compile_graph(graph)
            
            # --- 2. FIX: Initial state MUST use a real message object ---
            initial_state = AgentState(
                messages=[HumanMessage(content=initial_input, type='human')],
                current_task=initial_input,
                user=user, 
                context=context or {},
                next_agent=None,
                is_complete=False,
                supervisor_feedback=None,
                task_queue=[],
                completed_tasks=[],
                agent_outputs={},
                supervisor_decision=None
            )
            
            # Dump to dict for invocation
            state_dict = initial_state.model_dump(exclude_none=True)
            print("DEBUG: Initial state:", state_dict)
            
            result_state = compiled_graph.invoke(state_dict)
            
            # Hydrate messages from the result dict
            result_messages = _hydrate_messages(result_state.get('messages', []))

            clean_outputs = {}
            raw_outputs = result_state.get('agent_outputs', {})
            for agent_name, output_data in raw_outputs.items():
                clean_outputs[agent_name] = {
                    "response": output_data.get('response', 'No response content.')
                }

            if execution_log:
                for agent_name, output in raw_outputs.items():
                    ExecutionStep.objects.create(
                        execution=execution_log,
                        agent_name=agent_name,
                        input_data=output.get('input', ''), 
                        output_data=output.get('response', ''),
                        metadata=output
                    )
                
                final_message_content = result_messages[-1].content if result_messages else ''
                execution_log.final_output = str(final_message_content)
                execution_log.is_successful = True
                execution_log.save()
            
            # --- 3. FIX: Remove non-serializable user object ---
            if 'user' in result_state:
                del result_state['user']

            return {
                'success': True,
                'execution_id': execution_log.id if execution_log else None,
                'final_state': result_state,
                'messages': [str(msg.content) for msg in result_messages],
                'context': result_state.get('context', {}),
                'agent_outputs': clean_outputs,
                'total_executions': result_state.get('context', {}).get('execution_count', 0),
                'max_executions': self.max_executions
            }
            
        except Exception as e:
            logger.exception(f"Error running graph for user {user.id if user else 'Unknown'}: {e}")
            if execution_log:
                execution_log.error_message = str(e)
                execution_log.is_successful = False
                execution_log.save()
            
            return {
                'success': False,
                'execution_id': execution_log.id if execution_log else None,
                'error': str(e),
                'messages': [],
                'context': {}
            }

    def run_graph_stream(self, graph: Graph, initial_input: str, context: Dict = None, user=None):
        """
        Streams the execution of the graph, yielding JSON chunks for each step.
        """
        execution_log = None
        if user:
            execution_log = ExecutionLog.objects.create(
                graph=graph,
                user=user,
                initial_input=initial_input,
                context=context or {}
            )

        try:
            compiled_graph = self.graph_compiler.compile_graph(graph)
            
            initial_state = AgentState(
                messages=[HumanMessage(content=initial_input, type='human')],
                current_task=initial_input,
                user=user, 
                context=context or {},
                next_agent=None,
                is_complete=False,
                supervisor_feedback=None,
                task_queue=[],
                completed_tasks=[],
                agent_outputs={},
                supervisor_decision=None
            )
            
            state_dict = initial_state.model_dump(exclude_none=True)
            
            # Yield initial event
            yield json.dumps({
                "type": "start",
                "execution_id": execution_log.id if execution_log else None,
                "message": "Graph execution started."
            }) + "\n"

            # Stream the graph execution
            final_state = None
            for step_output in compiled_graph.stream(state_dict):
                # step_output is a dict where keys are node names and values are state updates
                for node_name, state_update in step_output.items():
                    
                    # Check for tool outputs or agent responses
                    if 'agent_outputs' in state_update:
                        outputs = state_update['agent_outputs']
                        for agent_name, output_data in outputs.items():
                            yield json.dumps({
                                "type": "agent_output",
                                "node": agent_name,
                                "output": output_data.get('response', '')
                            }) + "\n"
                            
                            # Log step
                            if execution_log:
                                ExecutionStep.objects.create(
                                    execution=execution_log,
                                    agent_name=agent_name,
                                    input_data=output_data.get('input', ''),
                                    output_data=output_data.get('response', ''),
                                    metadata=output_data
                                )

                    # Check for tool execution (custom logic in our wrapper prints to stdout, 
                    # but we can capture state changes here if needed)
                    if 'current_task' in state_update:
                         yield json.dumps({
                            "type": "update",
                            "node": node_name,
                            "message": f"Node {node_name} updated state."
                        }) + "\n"
                    
                    final_state = state_update # Keep track of the latest state

            # Final success event
            if execution_log:
                execution_log.is_successful = True
                execution_log.save()

            yield json.dumps({
                "type": "complete",
                "status": "success",
                "message": "Graph execution completed."
            }) + "\n"

        except Exception as e:
            logger.exception(f"Error streaming graph for user {user.id if user else 'Unknown'}: {e}")
            if execution_log:
                execution_log.error_message = str(e)
                execution_log.is_successful = False
                execution_log.save()
            
            yield json.dumps({
                "type": "error",
                "error": str(e)
            }) + "\n"