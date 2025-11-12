from typing import Dict, Any, List, Optional
import functools
from langgraph.graph import StateGraph, END
from ...agents.services.compiler import AgentCompiler, AgentState
from ..models import Graph
from ...agents.models import Agent
from ...executions.models import ExecutionLog, ExecutionStep

from ...tools.services.registry import TOOL_REGISTRY
from ...tools.models import Tool


class GraphCompiler:
    """
    Compiles a Graph model into an executable LangGraph
    by using the JSON data in the 'graph_data' field as the source of truth.
    """
    
    def __init__(self):
        self.agent_compiler = AgentCompiler()
    
    def compile_graph(self, graph: Graph) -> StateGraph:
        """Compile a Graph model into an executable LangGraph"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # 1. Get graph structure from the SAVED JSON ('graph_data')
        if 'nodes' not in graph.graph_data or not graph.graph_data['nodes']:
            raise ValueError("Graph data is empty or missing 'nodes' key. Cannot compile.")

        nodes_json = graph.graph_data.get('nodes', [])
        edges_json = graph.graph_data.get('edges', [])

        # Map React Flow ID to agent/tool name
        rf_id_to_agent_name_map = {}
        
        # List of available worker agents for supervisor prompt
        available_agent_nodes_for_prompt = []
        
        # 2. Compile and Add Nodes
        workflow.add_node("END", lambda state: state)
        supervisor_rf_id = None
        supervisor_name = None
        supervisor_agent = None

        for node in nodes_json:
            # --- MODIFICATION: Get node_type ---
            node_type = node.get('type', 'agent') # Default to 'agent' for older graphs
            
            # Get common data
            node_data = node.get('data', {})
            node_name = node_data.get('label') or node_data.get('name')
            rf_id = node.get('id')
            
            if not node_name or not rf_id:
                raise ValueError(f"Node {rf_id} is missing 'id' or 'label'/'name'.")

            # Map the React Flow ID to the agent's/tool's name
            rf_id_to_agent_name_map[rf_id] = node_name

            # --- MODIFICATION: Use if/elif for node types ---
            
            if node_type == 'agent':
                agent_db_id = node_data.get('id')
                agent_role = node_data.get('role', 'general')

                if not agent_db_id:
                    raise ValueError(f"Agent node {node_name} (ID: {rf_id}) is missing 'id' in its data property.")

                # Fetch agent from database
                try:
                    agent = Agent.objects.get(id=agent_db_id)
                    
                    if agent_role == 'supervisor':
                        supervisor_rf_id = rf_id
                        supervisor_name = node_name
                        supervisor_agent = agent
                    else:
                        available_agent_nodes_for_prompt.append(agent)
                        agent_node = self.agent_compiler.compile_agent(agent, graph_context={})
                        workflow.add_node(node_name, agent_node)
                        
                except Agent.DoesNotExist:
                    raise ValueError(f"Agent '{node_name}' (ID: {agent_db_id}) found in graph JSON but not in database.")

            # --- NEW: Handle tool nodes ---
            elif node_type == 'tool':
                tool_db_id = node_data.get('id')
                if not tool_db_id:
                    raise ValueError(f"Tool node {node_name} (ID: {rf_id}) is missing 'id' in its data property.")

                try:
                    # 1. Fetch the Tool from the database
                    tool = Tool.objects.get(id=tool_db_id)
                    
                    # 2. Look up its function from the registry
                    tool_type_key = tool.tool_type
                    base_tool_function = TOOL_REGISTRY.get(tool_type_key)
                    
                    if not base_tool_function:
                        raise ValueError(f"Tool type '{tool_type_key}' for tool '{node_name}' not found in TOOL_REGISTRY.")
                    
                    # 3. Get the tool's config
                    tool_config = tool.config or {}
                    
                    # 4. Create the node function by binding the config
                    #    This creates a new function that just takes 'state'
                    bound_tool_function = functools.partial(base_tool_function, config=tool_config)
                    
                    # 5. Add the bound function as a node
                    workflow.add_node(node_name, bound_tool_function)

                except Tool.DoesNotExist:
                    raise ValueError(f"Tool '{node_name}' (ID: {tool_db_id}) found in graph JSON but not in database.")

        # --- NOW compile the supervisor with the correct context (only once) ---
        if supervisor_name and supervisor_agent:
            graph_context = {
                'graph': graph,
                'available_agents': available_agent_nodes_for_prompt
            }
            # Compile the supervisor node with the full list of worker agents
            supervisor_node = self.agent_compiler.compile_agent(supervisor_agent, graph_context)
            workflow.add_node(supervisor_name, supervisor_node)

        
        # 3. Add Edges based on JSON
        nodes_with_outgoing_edges = set()
        
        if supervisor_name:
            # --- SUPERVISOR LOGIC ---
            # Build the routing map from the supervisor's outgoing edges
            routing_map = {"END": "END", "FINISH": "END"}
            
            for edge in edges_json:
                if edge.get('source') == supervisor_rf_id:
                    target_name = rf_id_to_agent_name_map.get(edge.get('target'))
                    if target_name:
                        routing_map[target_name] = target_name
                        nodes_with_outgoing_edges.add(supervisor_rf_id)
            
            # Define the router function
            def supervisor_router(state: AgentState) -> str:
                """Inspects the state and decides where to route."""
                print("\n" + "🔀"*40)
                print("SUPERVISOR ROUTER CALLED")
                print("🔀"*40)
                print(f"Execution count: {state.context.get('execution_count', 0)}")
                print(f"State has supervisor_decision: {state.supervisor_decision is not None}")
                print(f"Available routes: {list(routing_map.keys())}")
                
                if state.supervisor_decision:
                    decision = state.supervisor_decision
                    print(f"\n📋 Decision details:")
                    print(f"   - next_agent: {decision.get('next_agent')}")
                    print(f"   - is_complete: {decision.get('is_complete')}")
                    print(f"   - reasoning: {decision.get('reasoning', 'N/A')}")
                    
                    # Handle completion
                    if decision.get('is_complete') or decision.get('next_agent') == 'FINISH':
                        print(f"\n✅ ROUTING DECISION: END (task complete)")
                        print("🔀"*40 + "\n")
                        return "END"
                    
                    # Route to specified agent
                    next_agent = decision.get('next_agent')
                    if next_agent and next_agent in routing_map:
                        print(f"\n✅ ROUTING DECISION: {next_agent}")
                        print("🔀"*40 + "\n")
                        return next_agent
                    else:
                        print(f"\n⚠️  WARNING: next_agent '{next_agent}' not in routing_map!")
                        print(f"   Routing map keys: {list(routing_map.keys())}")
                        print(f"   Defaulting to END")
                        print("🔀"*40 + "\n")
                        return "END"
                else:
                    print("\n⚠️  WARNING: No supervisor_decision found in state!")
                
                # Fallback to END to prevent infinite loops
                print(f"\n⚠️  WARNING: Supervisor router fallback to END")
                print(f"   Decision was: {state.supervisor_decision}")
                print("🔀"*40 + "\n")
                return "END"

            # Add the conditional edge from supervisor
            workflow.add_conditional_edges(
                supervisor_name,
                supervisor_router,
                routing_map
            )

            # FIXED: Add return edges from all worker agents back to supervisor
            for agent in available_agent_nodes_for_prompt:
                workflow.add_edge(agent.name, supervisor_name)
                nodes_with_outgoing_edges.add(
                    # Find the RF ID for this agent
                    next((rf_id for rf_id, name in rf_id_to_agent_name_map.items() 
                          if name == agent.name), None)
                )
        
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
            # Fallback: find a node with no incoming edges
            nodes_with_incoming_edges = set(e.get('target') for e in edges_json)
            entry_node = next((n for n in nodes_json if n.get('id') not in nodes_with_incoming_edges), None)
            
            if not entry_node:
                if not nodes_json:
                    raise ValueError("Cannot determine entry point: Graph has no nodes.")
                entry_node = nodes_json[0]
                
            entry_point_name = rf_id_to_agent_name_map[entry_node.get('id')]
            workflow.set_entry_point(entry_point_name)
            

        # 5. Connect Leaf Nodes to END (only for non-supervisor graphs)
        # FIXED: In supervisor graphs, workers already return to supervisor
        if not supervisor_name:
            for node in nodes_json:
                if node.get('id') not in nodes_with_outgoing_edges:
                    agent_name = rf_id_to_agent_name_map[node.get('id')]
                    workflow.add_edge(agent_name, "END")

        # Compile and return the graph
        return workflow.compile()

class GraphRunner:
    """Executes compiled graphs and manages execution state"""
    
    def __init__(self):
        self.graph_compiler = GraphCompiler()
        self.active_executions = {}
    
    def run_graph(self, graph: Graph, initial_input: str, context: Dict = None, user=None) -> Dict[str, Any]:
        """Execute a graph with initial input"""
        
        # Create execution log
        execution_log = None
        if user:
            execution_log = ExecutionLog.objects.create(
                graph=graph,
                user=user,
                initial_input=initial_input,
                context=context or {}
            )
        
        try:
            # Compile the graph
            compiled_graph = self.graph_compiler.compile_graph(graph)
            
            # Create initial state using pydantic model
            initial_state = AgentState(
                messages=[],
                current_task=initial_input,
                context=context or {},
                next_agent=None,
                is_complete=False,
                supervisor_feedback=None,
                task_queue=[],
                completed_tasks=[],
                agent_outputs={}
            )
            
            # Convert to dict for invoke
            state_dict = initial_state.model_dump()
            print("DEBUG: Initial state:", state_dict)
            
            # Execute the graph
            result = compiled_graph.invoke(state_dict)
            
            # Log execution steps
            if execution_log:
                for agent_name, output in result.get('agent_outputs', {}).items():
                    ExecutionStep.objects.create(
                        execution=execution_log,
                        agent_name=agent_name,
                        input_data=output.get('input', ''),
                        output_data=output.get('response', ''),
                        metadata=output
                    )
                
                execution_log.final_output = str(result.get('messages', [])[-1] if result.get('messages') else '')
                execution_log.is_successful = True
                execution_log.save()
            
            return {
                'success': True,
                'execution_id': execution_log.id if execution_log else None,
                'final_state': result,
                'messages': [str(msg) for msg in result.get('messages', [])],
                'context': result.get('context', {}),
                'agent_outputs': result.get('agent_outputs', {})
            }
            
        except Exception as e:
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




"""
class GraphCompiler:
    Compiles a Graph model into an executable LangGraph
    
    def __init__(self):
        self.agent_compiler = AgentCompiler()
    
    def compile_graph(self, graph: Graph) -> StateGraph:
        Compile a Graph model into an executable LangGraph
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Get all agents and prepare context
        agents = graph.agents.all()
        available_agents = list(agents.exclude(role='supervisor'))
        
        graph_context = {
            'graph': graph,
            'available_agents': available_agents
        }
        
        # Compile all agents in the graph
        for agent in agents:
            agent_node = self.agent_compiler.compile_agent(agent, graph_context)
            workflow.add_node(agent.name, agent_node)
        
        # Add edges based on supervisor pattern
        self._add_supervisor_edges(workflow, graph)
        
        # Set entry point (supervisor or first agent)
        entry_agent = self._determine_entry_agent(graph)
        workflow.set_entry_point(entry_agent)
        
        # Compile and return the graph
        return workflow.compile()
    
    def _add_supervisor_edges(self, workflow: StateGraph, graph: Graph):
        Add supervisor-pattern edges
        graph_config = graph.graph_data
        
        # Get supervisor agent
        supervisor = graph.agents.filter(role='supervisor').first()
        if not supervisor:
            # No supervisor pattern - use simple sequential flow
            self._add_sequential_edges(workflow, graph)
            return
        
        supervisor_name = supervisor.name
        
        # Create routing map for supervisor
        routing_rules = graph_config.get('routing_rules', {}).copy()
        
        # Add all non-supervisor agents to routing
        worker_agents = graph.agents.exclude(role='supervisor')
        for agent in worker_agents:
            if agent.name not in routing_rules:
                routing_rules[agent.name] = agent.name
        
        # Add conditional edges from supervisor to all workers and END
        def supervisor_router(state: AgentState) -> str:
            next_node = self._determine_next_node(state, routing_rules)
            if next_node == END or next_node == 'FINISH':
                return 'FINISH'
            return next_node
        
        # Create the final routing map including both agents and END state
        final_routes = {**routing_rules, 'FINISH': END}
        
        workflow.add_conditional_edges(
            supervisor_name,
            supervisor_router,
            final_routes
        )
        
        # Add edges from all workers back to supervisor
        for agent in worker_agents:
            workflow.add_edge(agent.name, supervisor_name)
    
    def _add_sequential_edges(self, workflow: StateGraph, graph: Graph):
        Fallback: Add simple sequential edges when no supervisor
        agents = list(graph.agents.all())
        
        for i in range(len(agents) - 1):
            workflow.add_edge(agents[i].name, agents[i + 1].name)
        
        # Last agent ends
        if agents:
            workflow.add_edge(agents[-1].name, END)
    
    def _determine_entry_agent(self, graph: Graph) -> str:
        Determine which agent should be the entry point
        # Check graph_data for explicit entry point
        entry_point = graph.graph_data.get('entry_point')
        if entry_point:
            return entry_point
        
        # Default to supervisor agent
        supervisor = graph.agents.filter(role='supervisor').first()
        if supervisor:
            return supervisor.name
        
        # Fall back to first agent
        return graph.agents.first().name
    
    def _determine_next_node(self, state: AgentState, routes: Dict[str, str]) -> str:
        Supervisor-specific routing logic
        
        # Check if supervisor made an explicit decision
        if state.supervisor_decision:
            decision = state.supervisor_decision
            
            # Handle completion
            if decision.get('is_complete'):
                return 'FINISH'
            
            # Route to specified agent
            next_agent = decision.get('next_agent')
            if next_agent == 'FINISH':
                return 'FINISH'
            elif next_agent and next_agent in routes:
                return next_agent
        
        # Fallback: analyze the last message for routing cues
        if state.messages:
            last_message = state.messages[-1].content.lower()
            
            # Look for explicit routing in the message
            for route_key in routes:
                if route_key.lower() in last_message:
                    if route_key == 'FINISH':
                        return 'FINISH'
                    return route_key
        
        # Check if there are pending tasks
        if state.task_queue:
            # Route to the most appropriate agent for the next task
            available_routes = [r for r in routes.keys() if r != 'FINISH']
            if available_routes:
                return available_routes[0]
        
        # Default to completion if no clear routing
        return 'FINISH'
    
"""