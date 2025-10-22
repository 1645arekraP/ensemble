#!/usr/bin/env python
"""
Test script for graph serialization
Run with: python test_serialization.py
"""

import os
import sys
import django
import json

# Setup Django environment
if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
    django.setup()

from django.contrib.auth import get_user_model
from apps.graph.models import Graph
from apps.agents.models import Agent
from apps.tools.models import Tool


def test_serialization():
    """Test graph serialization with existing data"""
    print("🧪 Testing Graph Serialization\n")
    print("="*60)

    # Get any existing graph
    graphs = Graph.objects.all()

    if not graphs.exists():
        print("❌ No graphs found. Run test.py first to create demo graphs.")
        return

    print(f"📊 Found {graphs.count()} graph(s) in database\n")

    for graph in graphs:
        print(f"\n{'='*60}")
        print(f"🔍 Testing: {graph.name}")
        print(f"{'='*60}")

        # Test serialization
        try:
            serialized = graph.serialize()

            print(f"\n✅ Serialization successful!")
            print(f"\n📦 Serialized Structure:")
            print(json.dumps(serialized, indent=2))

            # Verify structure
            assert 'nodes' in serialized, "Missing 'nodes' key"
            assert 'edges' in serialized, "Missing 'edges' key"
            assert 'metadata' in serialized, "Missing 'metadata' key"

            print(f"\n📊 Stats:")
            print(f"   - Nodes: {len(serialized['nodes'])}")
            print(f"   - Edges: {len(serialized['edges'])}")
            print(f"   - Pattern: {serialized['metadata']['pattern']}")

            # Show node details
            if serialized['nodes']:
                print(f"\n🤖 Agents:")
                for node in serialized['nodes']:
                    tools = node['data'].get('tools', [])
                    tool_names = [t['name'] for t in tools]
                    print(f"   - {node['data']['label']} ({node['type']})")
                    if tool_names:
                        print(f"     Tools: {', '.join(tool_names)}")

            # Show edge details
            if serialized['edges']:
                print(f"\n🔗 Connections:")
                for edge in serialized['edges']:
                    print(f"   - {edge['source']} → {edge['target']} ({edge['type']})")

            # Test save to DB
            print(f"\n💾 Testing save to database...")
            serialized_saved = graph.serialize(save=True)
            graph.refresh_from_db()

            assert 'serialized' in graph.graph_data, "Serialized data not saved"
            print(f"   ✅ Saved to graph_data field")

            # Test get_serialized (cached)
            cached = graph.get_serialized()
            assert cached == serialized_saved, "Cached version doesn't match"
            print(f"   ✅ Cache retrieval works")

        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

    print(f"\n{'='*60}")
    print("✅ All serialization tests completed!")
    print("="*60)


if __name__ == '__main__':
    test_serialization()
