from typing import Dict, Any, List
from ..models import Graph


class GraphSerializer:
    """
    Serializes a Graph model into a frontend-compatible format for visualization.
    Uses a node-edge structure compatible with libraries like React Flow, vis.js, etc.
    """

    @staticmethod
    def serialize_graph(graph: Graph) -> Dict[str, Any]:
        """
        Convert a Graph model to a serializable format for frontend rendering.

        Returns a dictionary with:
        - nodes: List of agent nodes with their properties
        - edges: List of connections between nodes
        - metadata: Graph-level information
        """

        agents = graph.agents.all()
        nodes = []
        edges = []

        # Build nodes from agents
        for agent in agents:
            node = {
                'id': str(agent.id),
                'type': agent.role,  # 'supervisor' or 'general'
                'data': {
                    'label': agent.name,
                    'description': agent.description,
                    'provider': agent.provider,
                    'model': agent.model,
                    'tools': [
                        {
                            'id': tool.id,
                            'name': tool.name,
                            'type': tool.tool_type,
                            'description': tool.description
                        }
                        for tool in agent.tools.all()
                    ]
                },
                'position': agent.metadata.get('position', {'x': 0, 'y': 0})  # Store UI position
            }
            nodes.append(node)

        # Build edges based on graph pattern
        edges = GraphSerializer._build_edges(graph, agents)

        return {
            'nodes': nodes,
            'edges': edges,
            'metadata': {
                'name': graph.name,
                'description': graph.description,
                'pattern': GraphSerializer._detect_pattern(graph),
                'config': graph.graph_data
            }
        }

    @staticmethod
    def _build_edges(graph: Graph, agents) -> List[Dict[str, Any]]:
        """Build edges based on the graph's execution pattern"""
        edges = []

        # Check if supervisor pattern
        supervisor = agents.filter(role='supervisor').first()

        if supervisor:
            # Supervisor pattern: supervisor connects to all workers bidirectionally
            workers = agents.exclude(role='supervisor')

            for worker in workers:
                # Edge from supervisor to worker
                edges.append({
                    'id': f'e-{supervisor.id}-{worker.id}',
                    'source': str(supervisor.id),
                    'target': str(worker.id),
                    'type': 'conditional',  # Supervisor makes routing decisions
                    'label': 'route'
                })

                # Edge from worker back to supervisor
                edges.append({
                    'id': f'e-{worker.id}-{supervisor.id}',
                    'source': str(worker.id),
                    'target': str(supervisor.id),
                    'type': 'default',
                    'label': 'return'
                })
        else:
            # Sequential pattern: connect agents in order
            agent_list = list(agents)
            for i in range(len(agent_list) - 1):
                edges.append({
                    'id': f'e-{agent_list[i].id}-{agent_list[i + 1].id}',
                    'source': str(agent_list[i].id),
                    'target': str(agent_list[i + 1].id),
                    'type': 'default',
                    'label': 'next'
                })

        return edges

    @staticmethod
    def _detect_pattern(graph: Graph) -> str:
        """Detect the graph execution pattern"""
        if graph.agents.filter(role='supervisor').exists():
            return 'supervisor'
        return 'sequential'

    @staticmethod
    def save_serialized_graph(graph: Graph) -> Dict[str, Any]:
        """
        Serialize the graph and save it to the graph_data field.
        Returns the serialized data.
        """
        serialized = GraphSerializer.serialize_graph(graph)

        # Merge with existing graph_data (preserve runtime config)
        graph.graph_data = {
            **graph.graph_data,
            'serialized': serialized
        }
        graph.save()

        return serialized


