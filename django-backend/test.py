#!/usr/bin/env python
"""
MCP Server Integration Test
Run with: python test.py
"""

import os
import sys
import django

# Setup Django environment
if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()

from django.contrib.auth import get_user_model
from apps.agents.models import Agent
from apps.graph.models import Graph
from apps.tools.models import mcp
from apps.graph.services.runner import GraphRunner


def setup_user():
    """Create or get test user"""
    User = get_user_model()
    user, created = User.objects.get_or_create(
        email='mcp_test@example.com',
        defaults={'first_name': 'MCP', 'last_name': 'Tester'}
    )
    print(f"{'✅ Created' if created else '📋 Using'} user: {user.email}\n")
    return user


def create_mcp_server():
    """Create or get MCP server configuration"""
    print("🔧 Setting up MCP server...")

    # You can configure your MCP server URL here
    mcp_server, created = mcp.objects.get_or_create(
        name='filesystem',
        defaults={
            'description': 'Greet someone via MCP protocol',
            'url': 'http://localhost:8000'  # Change this to your MCP server URL
        }
    )

    print(f"{'✅ Created' if created else '📋 Using'} MCP server: {mcp_server.name}")
    print(f"   URL: {mcp_server.url}")
    print(f"   Description: {mcp_server.description}\n")

    return mcp_server


def create_mcp_test_graph(user, mcp_server):
    """Create a simple graph with MCP-enabled agent"""
    print("📊 Setting up test graph...")

    # Delete old test graph and agents if they exist
    Graph.objects.filter(owner=user, name="MCP Test Graph").delete()
    Agent.objects.filter(user=user, name__in=['mcp_supervisor', 'mcp_worker']).delete()
    print("🗑️  Deleted old graph and agents (if any)")

    # First, create agents
    supervisor = Agent.objects.create(
        user=user,
        name='mcp_supervisor',
        description='Coordinates MCP tasks',
        system_instruction_prompt='''You are a supervisor coordinating MCP-based tasks.

You have one agent available:
- mcp_worker: Has access to MCP server tools for greeting people

Your job is to delegate work to the appropriate agent.

IMPORTANT:
- When you receive a greeting request, you MUST route to "mcp_worker" first
- The mcp_worker will use the MCP tools to complete the greeting
- Only use FINISH after the worker has completed their task

<decision>
next_agent: [mcp_worker/FINISH]
is_complete: [true/false]
reasoning: [brief explanation]
</decision>''',
        role=Agent.AgentRole.SUPERVISOR,
        provider=Agent.AgentProvider.OPENAI,
        model='gpt-4o'
    )

    # Create MCP worker with MCP server access
    mcp_worker = Agent.objects.create(
        user=user,
        name='mcp_worker',
        description='Executes tasks using MCP server tools',
        system_instruction_prompt='''You are a worker agent with access to MCP server tools for greeting people.

IMPORTANT: You MUST use the MCP tools available to you. Do not just respond with text.

When given a greeting task:
1. Look at the available tools (they will be from the MCP server)
2. Use the appropriate greeting tool with the person's name
3. Report the result from the tool
4. Explain what you did

Remember: You have tools available - use them!''',
        role=Agent.AgentRole.GENERAL,
        provider=Agent.AgentProvider.OPENAI,
        model='gpt-4o'
    )

    # Connect MCP server to the worker
    mcp_worker.mcp.add(mcp_server)

    # Now create graph with proper ReactFlow structure
    graph = Graph.objects.create(
        owner=user,
        name="MCP Test Graph",
        description="Simple graph to test MCP server integration",
        graph_data={
                'nodes': [
                    {
                        'id': 'supervisor-1',
                        'type': 'agent',
                        'data': {
                            'id': supervisor.id,
                            'label': supervisor.name,
                            'name': supervisor.name,
                            'role': 'supervisor'
                        }
                    },
                    {
                        'id': 'worker-1',
                        'type': 'agent',
                        'data': {
                            'id': mcp_worker.id,
                            'label': mcp_worker.name,
                            'name': mcp_worker.name,
                            'role': 'general'
                        }
                    }
                ],
                'edges': [
                    {
                        'id': 'e1',
                        'source': 'supervisor-1',
                        'target': 'worker-1',
                        'data': {'label': 'route_to_worker'}
                    }
                ]
            }
    )

    print(f"✅ Created graph: {graph.name}")
    print(f"   Supervisor: {supervisor.name}")
    print(f"   Worker: {mcp_worker.name} (with MCP server: {mcp_server.name})\n")

    return graph


def run_mcp_test(graph, user):
    """Run MCP integration test"""
    print("="*60)
    print("🚀 Running MCP Server Test")
    print("="*60)

    # Test input - explicit request to use MCP tool
    test_input = "Please greet Parker using the MCP greeting tool"

    print(f"📝 Test Input: {test_input}\n")
    print("⏳ Executing graph...\n")

    try:
        runner = GraphRunner()
        result = runner.run_graph(
            graph=graph,
            initial_input=test_input,
            user=user
        )

        print("\n" + "="*60)
        if result['success']:
            print("✅ TEST PASSED\n")

            # Show agent outputs
            if result.get('agent_outputs'):
                print("📊 Agent Execution Details:\n")
                for agent_name, output in result['agent_outputs'].items():
                    print(f"🤖 {agent_name.upper()}:")
                    print(f"   Role: {output.get('agent_role', 'N/A')}")
                    print(f"   Timestamp: {output.get('timestamp', 'N/A')}")

                    response = output.get('response', '')
                    if response:
                        print(f"   Response: {response[:300]}...")
                    print()

            # Show final state
            if result.get('state'):
                print(f"📋 Final State:")
                print(f"   Complete: {result['state'].get('is_complete', False)}")
                print(f"   Next Agent: {result['state'].get('next_agent', 'N/A')}")

            # Show execution ID
            if result.get('execution_id'):
                print(f"\n💾 Execution logged with ID: {result['execution_id']}")
        else:
            print("❌ TEST FAILED\n")
            print(f"Error: {result.get('error', 'Unknown error')}")

        print("="*60)

    except Exception as e:
        print("\n" + "="*60)
        print("❌ EXCEPTION OCCURRED\n")
        print(f"Error: {str(e)}\n")
        print("Full traceback:")
        print("-"*60)
        import traceback
        traceback.print_exc()
        print("="*60)


def main():
    """Main test function"""
    print("\n" + "="*60)
    print("🧪 MCP SERVER INTEGRATION TEST")
    print("="*60 + "\n")

    # Check for OpenAI API key
    from django.conf import settings
    if not settings.OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not found!")
        print("   Set it in your .env file: OPENAI_API_KEY='your-key-here'\n")
        return

    print("📋 Prerequisites:")
    print("   ✓ Django configured")
    print("   ✓ OpenAI API key found")
    print()

    print("💡 Before running this test:")
    print("   1. Make sure your MCP server is running")
    print("   2. Update the MCP server URL in this script if needed")
    print("   3. Default URL: http://localhost:3000")
    print()

    try:
        # Setup
        user = setup_user()
        mcp_server = create_mcp_server()
        graph = create_mcp_test_graph(user, mcp_server)

        # Run test
        run_mcp_test(graph, user)

        print("\n" + "="*60)
        print("🎉 Test Complete!")
        print("="*60)
        print("\n💡 Next steps:")
        print("   - Check the output above for MCP tool execution")
        print("   - Verify MCP server received the requests")
        print("   - Check database for ExecutionLog and ExecutionStep entries")
        print()

    except Exception as e:
        print("\n" + "="*60)
        print("❌ SETUP FAILED")
        print("="*60)
        print(f"\nError: {str(e)}\n")
        import traceback
        traceback.print_exc()
        print()


if __name__ == '__main__':
    main()
