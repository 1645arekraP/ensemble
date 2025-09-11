#!/usr/bin/env python
"""
Test script for the multi-agent system
Run with: python test_agents.py
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
if __name__ == '__main__':
    # Add your project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Configure Django settings - adjust this path to your settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()

# Now import Django models after setup
from django.contrib.auth import get_user_model
from apps.agents.models import Agent
from apps.graph.models import Graph
from apps.tools.models import Tool
from apps.graph.services.runner import GraphRunner
import json
from datetime import datetime


def create_demo_user():
    """Create or get a demo user"""
    User = get_user_model()
    user, created = User.objects.get_or_create(
        email='demo@example.com',
        defaults={
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    
    if created:
        print(f"✅ Created demo user: {user.email}")
    else:
        print(f"📋 Using existing user: {user.email}")
    
    return user


def create_demo_tools():
    """Create demo tools"""
    print("\n🔧 Setting up tools...")
    
    # Web search tool
    search_tool, created = Tool.objects.get_or_create(
        name='web_search',
        defaults={
            'description': 'Search the web for information',
            'tool_type': 'web_search',
            'function_schema': {
                'type': 'function',
                'function': {
                    'name': 'web_search',
                    'description': 'Search the web for information',
                    'parameters': {
                        'type': 'object',
                        'properties': {
                            'query': {
                                'type': 'string',
                                'description': 'Search query'
                            }
                        },
                        'required': ['query']
                    }
                }
            }
        }
    )
    
    if created:
        print(f"  ✅ Created search tool")
    else:
        print(f"  📋 Using existing search tool")
    
    return search_tool


def create_demo_graph(user, search_tool):
    """Create a demo supervisor graph"""
    print("\n📊 Setting up graph...")
    
    # Create or get the graph
    graph, created = Graph.objects.get_or_create(
        owner=user,
        name="Content Creation Team",
        defaults={
            'description': "A supervisor-led team for creating research-based content",
            'graph_data': {
                'supervisor': 'supervisor',
                'routing_rules': {
                    'researcher': 'researcher',
                    'writer': 'writer', 
                    'reviewer': 'reviewer',
                    'FINISH': 'END'
                },
                'max_iterations': 10
            }
        }
    )
    
    if created:
        print(f"  ✅ Created graph: {graph.name}")
        
        # Create supervisor agent
        supervisor = Agent.objects.create(
            project=graph,
            name='supervisor',
            description='Coordinates the content creation workflow',
            system_instruction_prompt='''You are a content creation supervisor managing a team of specialists:

- researcher: Gathers information and conducts research on any topic
- writer: Creates well-structured written content based on research  
- reviewer: Reviews and improves content quality, checking for accuracy and clarity

Your responsibilities:
1. Analyze incoming requests and determine the workflow
2. Route tasks to the appropriate team member
3. Coordinate handoffs between team members  
4. Decide when the work is complete

Always end your response with a decision in this format:
<decision>
next_agent: [researcher/writer/reviewer/FINISH]
reason: [why you chose this agent]
is_complete: [true/false]
</decision>

Be strategic about the workflow. Usually: research → write → review → done.''',
            role=Agent.AgentRole.SUPERVISOR,
            provider=Agent.AgentProvider.OPENAI,
            model='gpt-4o'
        )
        print(f"    ✅ Created supervisor: {supervisor.name}")
        
        # Create researcher agent
        researcher = Agent.objects.create(
            project=graph,
            name='researcher', 
            description='Conducts thorough research on assigned topics',
            system_instruction_prompt='''You are a research specialist. Your responsibilities:

1. Gather comprehensive, accurate information on assigned topics
2. Find credible sources and identify key facts
3. Organize findings in a clear, structured format
4. Provide research summaries that others can build upon

Focus on:
- Accuracy and credibility of sources
- Comprehensive coverage of the topic
- Clear organization of information
- Actionable insights for content creation

Be thorough but concise. Always cite your reasoning.''',
            role=Agent.AgentRole.GENERAL,
            provider=Agent.AgentProvider.OPENAI,
            model='gpt-4o'
        )
        researcher.tools.add(search_tool)
        print(f"    ✅ Created researcher: {researcher.name}")
        
        # Create writer agent
        writer = Agent.objects.create(
            project=graph,
            name='writer',
            description='Creates high-quality written content',
            system_instruction_prompt='''You are a writing specialist. Your responsibilities:

1. Transform research and information into engaging, well-structured content
2. Maintain consistent tone, style, and voice
3. Ensure content flows logically and is easy to read
4. Create content appropriate for the intended audience

Focus on:
- Clear, engaging writing style
- Logical structure and flow
- Proper formatting and organization
- Meeting the specific requirements of the task

Use the research provided to create compelling, accurate content.''',
            role=Agent.AgentRole.GENERAL,
            provider=Agent.AgentProvider.OPENAI,
            model='gpt-4o'
        )
        print(f"    ✅ Created writer: {writer.name}")
        
        # Create reviewer agent
        reviewer = Agent.objects.create(
            project=graph,
            name='reviewer',
            description='Reviews and improves content quality',
            system_instruction_prompt='''You are a content reviewer and editor. Your responsibilities:

1. Review content for accuracy, clarity, and completeness
2. Check that content meets the original requirements
3. Identify areas for improvement in structure, flow, and readability
4. Ensure the final content is polished and professional

Focus on:
- Factual accuracy and consistency
- Clear communication and readability
- Proper structure and organization
- Meeting the original brief and requirements

Provide specific, constructive feedback and improvements.''',
            role=Agent.AgentRole.GENERAL,
            provider=Agent.AgentProvider.OPENAI,
            model='gpt-4o'
        )
        print(f"    ✅ Created reviewer: {reviewer.name}")
        
    else:
        print(f"  📋 Using existing graph: {graph.name}")
    
    return graph


def test_simple_graph(user):
    """Create and test a simple 2-agent supervisor graph"""
    print("\n🧪 Creating simple test graph...")
    
    # Create simple graph
    simple_graph, created = Graph.objects.get_or_create(
        owner=user,
        name="Simple Test Team",
        defaults={
            'description': "Simple supervisor + worker for testing",
            'graph_data': {
                'supervisor': 'simple_supervisor',
                'routing_rules': {
                    'worker': 'worker',
                    'FINISH': 'END'
                },
                'max_iterations': 5
            }
        }
    )
    
    if created:
        # Create simple supervisor
        Agent.objects.create(
            project=simple_graph,
            name='simple_supervisor',
            description='Simple test supervisor',
            system_instruction_prompt='''You coordinate simple tasks. You have one worker agent available.

Analyze the task and decide:
- Route to "worker" if work needs to be done
- Mark complete when task is finished

<decision>
next_agent: [worker/FINISH]  
reason: [your reasoning]
is_complete: [true/false]
</decision>''',
            role=Agent.AgentRole.SUPERVISOR,
            provider=Agent.AgentProvider.OPENAI,
            model='gpt-4o'
        )
        
        # Create simple worker
        Agent.objects.create(
            project=simple_graph,
            name='worker',
            description='Simple test worker',
            system_instruction_prompt='You are a helpful worker. Complete the assigned task efficiently and clearly.',
            role=Agent.AgentRole.GENERAL,
            provider=Agent.AgentProvider.OPENAI,
            model='gpt-4o'
        )
        
        print(f"  ✅ Created simple graph: {simple_graph.name}")
    else:
        print(f"  📋 Using existing simple graph")
    
    return simple_graph


def run_test(graph, test_input, test_name="Test"):
    """Run a test with the given graph and input"""
    print(f"\n🚀 Running {test_name}...")
    print(f"📝 Input: {test_input}")
    print("="*60)
    
    try:
        # Create runner and execute
        runner = GraphRunner()
        result = runner.run_graph(
            graph=graph,
            initial_input=test_input,
            user=graph.owner
        )
        
        if result['success']:
            print("✅ SUCCESS!")
            
            # Show agent outputs
            if result.get('agent_outputs'):
                print("\n📊 Agent Execution Summary:")
                for agent_name, output in result['agent_outputs'].items():
                    print(f"\n🤖 {agent_name.upper()}:")
                    response = output.get('response', '')
                    if len(response) > 200:
                        print(f"   {response[:200]}...")
                        print(f"   [Response truncated - {len(response)} chars total]")
                    else:
                        print(f"   {response}")
            
            # Show final result
            messages = result.get('messages', [])
            if messages:
                print(f"\n🎯 FINAL OUTPUT:")
                print("-" * 40)
                print(messages[-1])
            
            if result.get('execution_id'):
                print(f"\n📋 Logged as execution ID: {result['execution_id']}")
                
        else:
            print(f"❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print("\n💥 EXCEPTION DETAILS:")
        print("-" * 60)
        import traceback
        traceback.print_exc()
        print("\nError message:", str(e))
        print("-" * 60)
    
    print("="*60)


def main():
    """Main test function"""
    print("🎬 Starting Multi-Agent System Test")
    print("=" * 50)
    
    # Check environment
    if not settings.OPENAI_API_KEY:
        print("⚠️  WARNING: OPENAI_API_KEY not found in settings")
        print("   Add it to your .env file as: OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        # Setup
        user = create_demo_user()
        search_tool = create_demo_tools()
        
        # Test 1: Simple graph
        print("\n" + "="*50)
        print("TEST 1: Simple Supervisor Pattern")
        print("="*50)
        
        simple_graph = test_simple_graph(user)
        run_test(
            simple_graph, 
            "Hello, please write a short greeting message.",
            "Simple Test"
        )
        
        # Test 2: Complex content creation
        print("\n" + "="*50) 
        print("TEST 2: Content Creation Team")
        print("="*50)
        
        content_graph = create_demo_graph(user, search_tool)
        run_test(
            content_graph,
            "Write a short article about the benefits of renewable energy, including some statistics.",
            "Content Creation Test"
        )
        
        # Test 3: Different task type
        print("\n" + "="*50)
        print("TEST 3: Research Task")
        print("="*50)
        
        run_test(
            content_graph,
            "Research and summarize the current state of electric vehicle adoption worldwide.",
            "Research Test"
        )
        
        print("\n🎉 All tests completed!")
        print("\n📊 Check your database for execution logs:")
        print("   - ExecutionLog: Overall graph runs")
        print("   - ExecutionStep: Individual agent executions")
        
    except Exception as e:
        print("\n💥 Setup failed. Full error trace:")
        print("="*50)
        import traceback
        traceback.print_exc()
        print("="*50)
        print("Error message:", str(e))
        print("Error type:", type(e).__name__)

if __name__ == '__main__':
    main()