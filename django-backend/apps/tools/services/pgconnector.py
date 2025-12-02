import logging
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from apps.credentials.models import UserCredential, Tool, decrypt_secret

logger = logging.getLogger(__name__)

def _get_db_connection(user):
    """Helper to get a PostgreSQL database connection using user credentials."""
    try:
        credential = UserCredential.objects.get(
            user=user,
            credential_type=Tool.ToolType.POSTGRES
        )

        # Decrypt connection details
        # We'll store connection info as JSON in encrypted_access_token
        connection_info = json.loads(decrypt_secret(credential.encrypted_access_token))

        conn = psycopg2.connect(
            host=connection_info.get('host'),
            port=connection_info.get('port', 5432),
            database=connection_info.get('database'),
            user=connection_info.get('user'),
            password=connection_info.get('password'),
            connect_timeout=10
        )
        return conn
    except UserCredential.DoesNotExist:
        return None
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        return None

def _execute_query(conn, query: str, params: tuple = None) -> str:
    """Executes a SQL query and returns results."""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)

            # Check if query returns results (SELECT, SHOW, etc.)
            if cursor.description:
                results = cursor.fetchall()
                if not results:
                    return "Query executed successfully. No rows returned."

                # Convert to list of dicts for JSON serialization
                rows = [dict(row) for row in results]
                return json.dumps(rows, indent=2, default=str)
            else:
                # For INSERT, UPDATE, DELETE, etc.
                conn.commit()
                return f"Query executed successfully. Rows affected: {cursor.rowcount}"

    except Exception as e:
        conn.rollback()
        logger.error(f"Query execution error: {e}")
        return f"Error executing query: {str(e)}"

def _list_tables(conn) -> str:
    """Lists all tables in the current database."""
    query = """
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """
    return _execute_query(conn, query)

def _describe_table(conn, table_name: str) -> str:
    """Describes the structure of a specific table."""
    # Get column information
    query = """
        SELECT
            column_name,
            data_type,
            character_maximum_length,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position;
    """

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (table_name,))
            columns = cursor.fetchall()

            if not columns:
                return f"Table '{table_name}' not found or has no columns."

            # Get primary keys
            pk_query = """
                SELECT a.attname
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary;
            """
            cursor.execute(pk_query, (table_name,))
            primary_keys = [row['attname'] for row in cursor.fetchall()]

            # Format output
            output = [f"Table: {table_name}\n", "Columns:"]
            for col in columns:
                pk_marker = " (PRIMARY KEY)" if col['column_name'] in primary_keys else ""
                data_type = col['data_type']
                if col['character_maximum_length']:
                    data_type += f"({col['character_maximum_length']})"
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""

                output.append(f"  - {col['column_name']}: {data_type} {nullable}{default}{pk_marker}")

            return "\n".join(output)

    except Exception as e:
        logger.error(f"Error describing table: {e}")
        return f"Error describing table '{table_name}': {str(e)}"

def _test_connection(conn) -> str:
    """Tests the database connection."""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            return f"Connection successful!\nPostgreSQL version: {version}"
    except Exception as e:
        return f"Connection test failed: {str(e)}"

def postgres_tool(state: dict, config: dict = None) -> dict:
    """
    Dispatcher tool for PostgreSQL database actions.
    Expected input (state.current_task) format:
    JSON string: {"action": "execute_query", "query": "SELECT * FROM users LIMIT 10"}
    OR {"action": "list_tables"}
    OR {"action": "describe_table", "table_name": "users"}
    OR {"action": "test_connection"}
    """
    logger.info(f"--- Running Tool: postgres_tool ---")

    # Handle state being a dict or object
    if isinstance(state, dict):
        user = state.get('user')
    else:
        user = getattr(state, 'user', None)

    if not user:
        return {"current_task": "Error: User not authenticated for tool."}

    conn = _get_db_connection(user)
    if not conn:
        return {"current_task": "Error: PostgreSQL not connected. Please add database credentials on the Connections page."}

    if isinstance(state, dict):
        input_str = state.get('current_task', '')
    else:
        input_str = getattr(state, 'current_task', '')

    # Default to test connection if empty or not JSON
    action = 'test_connection'
    params = {}

    try:
        if input_str.strip().startswith('{'):
            data = json.loads(input_str)
            action = data.get('action', 'test_connection')
            params = data
        else:
            logger.info(f"PostgreSQL tool received non-JSON input: {input_str}. Defaulting to test_connection.")
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse PostgreSQL tool input as JSON: {input_str}")

    output = ""
    try:
        if action == 'execute_query':
            query = params.get('query', '')
            if not query:
                output = "Error: No query provided."
            else:
                output = _execute_query(conn, query)
        elif action == 'list_tables':
            output = _list_tables(conn)
        elif action == 'describe_table':
            table_name = params.get('table_name', '')
            if not table_name:
                output = "Error: No table_name provided."
            else:
                output = _describe_table(conn, table_name)
        elif action == 'test_connection':
            output = _test_connection(conn)
        else:
            output = f"Error: Unknown PostgreSQL action '{action}'"

    except Exception as e:
        logger.error(f"PostgreSQL tool error: {e}")
        output = f"Error executing PostgreSQL action: {e}"
    finally:
        if conn:
            conn.close()

    return {"current_task": output}
