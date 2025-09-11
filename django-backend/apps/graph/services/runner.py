from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from ...agents.services.compiler import AgentCompiler, AgentState
from ..models import Graph
from ...executions.models import ExecutionLog, ExecutionStep


class GraphCompiler:
    """Compiles a Graph model into an executable LangGraph"""
    
    def __init__(self):
        self.agent_compiler = AgentCompiler()
    
    def compile_graph(self, graph: Graph) -> StateGraph:
        """Compile a Graph model into an executable LangGraph"""
        
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
        """Add supervisor-pattern edges"""
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
        """Fallback: Add simple sequential edges when no supervisor"""
        agents = list(graph.agents.all())
        
        for i in range(len(agents) - 1):
            workflow.add_edge(agents[i].name, agents[i + 1].name)
        
        # Last agent ends
        if agents:
            workflow.add_edge(agents[-1].name, END)
    
    def _determine_entry_agent(self, graph: Graph) -> str:
        """Determine which agent should be the entry point"""
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
        """Supervisor-specific routing logic"""
        
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

