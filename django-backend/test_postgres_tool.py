"""
Test script for the PostgreSQL connector tool.
Run this from the django-backend directory with: python test_postgres_tool.py
"""

import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.credentials.models import UserCredential, Tool, encrypt_secret
from apps.tools.services.pgconnector import postgres_tool

User = get_user_model()

def setup_test_credential(user, db_config):
    """
    Creates a test PostgreSQL credential for the user.
    """
    # Delete existing postgres credentials for this user
    UserCredential.objects.filter(
        user=user,
        credential_type=Tool.ToolType.POSTGRES
    ).delete()

    # Create new credential with encrypted connection info
    connection_info = json.dumps({
        "host": db_config.get("host", "localhost"),
        "port": db_config.get("port", 5432),
        "database": db_config.get("database"),
        "user": db_config.get("user"),
        "password": db_config.get("password"),
    })

    credential = UserCredential.objects.create(
        user=user,
        credential_type=Tool.ToolType.POSTGRES,
        encrypted_access_token=encrypt_secret(connection_info)
    )

    print(f"✓ Created PostgreSQL credential for user: {user.email}")
    return credential

def test_connection(user):
    """Test 1: Test database connection"""
    print("\n--- Test 1: Testing Connection ---")
    state = {
        'user': user,
        'current_task': json.dumps({"action": "test_connection"})
    }
    result = postgres_tool(state, {})
    print(f"Result: {result['current_task']}")
    return "Connection successful" in result['current_task']

def test_list_tables(user):
    """Test 2: List all tables"""
    print("\n--- Test 2: Listing Tables ---")
    state = {
        'user': user,
        'current_task': json.dumps({"action": "list_tables"})
    }
    result = postgres_tool(state, {})
    print(f"Result: {result['current_task'][:500]}...")  # Print first 500 chars
    return "Error" not in result['current_task']

def test_execute_query(user):
    """Test 3: Execute a simple query"""
    print("\n--- Test 3: Executing Query (SELECT version) ---")
    state = {
        'user': user,
        'current_task': json.dumps({
            "action": "execute_query",
            "query": "SELECT version();"
        })
    }
    result = postgres_tool(state, {})
    print(f"Result: {result['current_task'][:300]}...")
    return "Error" not in result['current_task']

def test_describe_table(user, table_name="auth_user"):
    """Test 4: Describe a table (using Django's auth_user table)"""
    print(f"\n--- Test 4: Describing Table '{table_name}' ---")
    state = {
        'user': user,
        'current_task': json.dumps({
            "action": "describe_table",
            "table_name": table_name
        })
    }
    result = postgres_tool(state, {})
    print(f"Result: {result['current_task'][:500]}...")
    return "Error" not in result['current_task'] or "not found" in result['current_task']

def test_create_and_query_table(user):
    """Test 5: Create a test table, insert data, and query it"""
    print("\n--- Test 5: Create Table, Insert, and Query ---")

    # Create table
    print("Creating test table...")
    state = {
        'user': user,
        'current_task': json.dumps({
            "action": "execute_query",
            "query": """
                DROP TABLE IF EXISTS test_postgres_tool;
                CREATE TABLE test_postgres_tool (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """
        })
    }
    result = postgres_tool(state, {})
    print(f"Create table result: {result['current_task']}")

    # Insert data
    print("\nInserting test data...")
    state['current_task'] = json.dumps({
        "action": "execute_query",
        "query": """
            INSERT INTO test_postgres_tool (name)
            VALUES ('Test 1'), ('Test 2'), ('Test 3');
        """
    })
    result = postgres_tool(state, {})
    print(f"Insert result: {result['current_task']}")

    # Query data
    print("\nQuerying test data...")
    state['current_task'] = json.dumps({
        "action": "execute_query",
        "query": "SELECT * FROM test_postgres_tool ORDER BY id;"
    })
    result = postgres_tool(state, {})
    print(f"Query result: {result['current_task']}")

    # Cleanup
    print("\nCleaning up test table...")
    state['current_task'] = json.dumps({
        "action": "execute_query",
        "query": "DROP TABLE test_postgres_tool;"
    })
    result = postgres_tool(state, {})
    print(f"Cleanup result: {result['current_task']}")

    return "Error" not in result['current_task']

def main():
    print("=" * 60)
    print("PostgreSQL Tool Test Suite")
    print("=" * 60)

    # Get or create a test user
    try:
        user = User.objects.first()
        if not user:
            print("No users found. Creating test user...")
            user = User.objects.create_user(
                email="test@example.com",
                password="testpass123",
                first_name="Test",
                last_name="User"
            )
        print(f"Using user: {user.email}")
    except Exception as e:
        print(f"Error getting user: {e}")
        return

    # Database configuration (update these values)
    print("\n" + "=" * 60)
    print("Database Configuration")
    print("=" * 60)

    db_config = {}

    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    print(f"Password: {'*' * len(db_config['password'])}")

    # Setup test credential
    try:
        setup_test_credential(user, db_config)
    except Exception as e:
        print(f"✗ Error setting up credential: {e}")
        return

    # Run tests
    print("\n" + "=" * 60)
    print("Running Tests")
    print("=" * 60)

    tests = [
        ("Connection Test", lambda: test_connection(user)),
        ("List Tables", lambda: test_list_tables(user)),
        ("Execute Query", lambda: test_execute_query(user)),
        ("Describe Table", lambda: test_describe_table(user)),
        ("Create/Insert/Query", lambda: test_create_and_query_table(user)),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results.append((test_name, False))
            print(f"\n✗ FAILED: {test_name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {test_name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

    # Cleanup credential
    print("\n" + "=" * 60)
    print("Cleaning up test credential...")
    UserCredential.objects.filter(
        user=user,
        credential_type=Tool.ToolType.POSTGRES
    ).delete()
    print("✓ Cleanup complete")

if __name__ == "__main__":
    main()
