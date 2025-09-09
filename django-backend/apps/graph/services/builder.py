from typing import Dict, Any, List
from ..models import Graph

class SupervisorGraphBuilder:
    """Helper for building supervisor-pattern graphs"""
    
    @staticmethod
    def create_supervisor_graph(
        user,
        name: str,
        description: str,
        supervisor_config: Dict[str, Any],
        worker_configs: List[Dict[str, Any]]
    ) -> Graph:
        """Create a complete supervisor graph with agents"""
        
        from ...agents.models import Agent
        
        # Create the graph
        graph = Graph.objects.create(
            owner=user,
            name=name,
            description=description,
            graph_data={
                'supervisor': supervisor_config['name'],
                'routing_rules': {
                    worker['name']: worker['name'] for worker in worker_configs
                },
                'max_iterations': 10
            }
        )
        
        # Create supervisor agent
        Agent.objects.create(
            project=graph,
            name=supervisor_config['name'],
            description=supervisor_config['description'],
            system_instruction_prompt=supervisor_config['system_instruction'],
            role='supervisor',
            provider=supervisor_config['provider'],
            model=supervisor_config['model']
        )
        
        # Create worker agents
        for worker_config in worker_configs:
            Agent.objects.create(
                project=graph,
                name=worker_config['name'],
                description=worker_config['description'],
                system_instruction_prompt=worker_config['system_instruction'],
                role='general',
                provider=worker_config['provider'],
                model=worker_config['model']
            )
        
        return graph