"""
Example usage script demonstrating how to use the PostgreSQL MCP Server.
This script shows how to interact with the server programmatically.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_client import PostgreSQLMCPClient


async def example_natural_language_query():
    """Example: Query database using natural language."""
    print("=== Natural Language Query Example ===\n")
    
    # Use absolute path from project root
    project_root = Path(__file__).parent.parent
    client = PostgreSQLMCPClient(["python", str(project_root / "mcp_server.py")])
    
    questions = [
        "How many tables are in the database?",
        "What are the names of all tables?",
        "Show me the schema of the users table",
    ]
    
    for question in questions:
        print(f"Question: {question}")
        try:
            result = await client.natural_language_query(question)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")


async def example_sql_query():
    """Example: Execute direct SQL query."""
    print("=== Direct SQL Query Example ===\n")
    
    # Use absolute path from project root
    project_root = Path(__file__).parent.parent
    client = PostgreSQLMCPClient(["python", str(project_root / "mcp_server.py")])
    
    queries = [
        "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public'",
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 5",
    ]
    
    for query in queries:
        print(f"SQL: {query}")
        try:
            result = await client.sql_query(query)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")


async def example_list_tables():
    """Example: List all tables."""
    print("=== List Tables Example ===\n")
    
    # Use absolute path from project root
    project_root = Path(__file__).parent.parent
    client = PostgreSQLMCPClient(["python", str(project_root / "mcp_server.py")])
    
    try:
        result = await client.list_tables()
        print(f"Tables: {result}\n")
    except Exception as e:
        print(f"Error: {e}\n")


async def example_describe_table():
    """Example: Describe table schema."""
    print("=== Describe Table Example ===\n")
    
    # Use absolute path from project root
    project_root = Path(__file__).parent.parent
    client = PostgreSQLMCPClient(["python", str(project_root / "mcp_server.py")])
    
    # First, get list of tables
    try:
        tables_result = await client.list_tables()
        if tables_result.get("success") and tables_result.get("tables"):
            table_name = tables_result["tables"][0]["table_name"]
            print(f"Describing table: {table_name}")
            result = await client.describe_table(table_name)
            print(f"Schema: {result}\n")
        else:
            print("No tables found in database\n")
    except Exception as e:
        print(f"Error: {e}\n")


async def main():
    """Run all examples."""
    print("PostgreSQL MCP Server - Example Usage\n")
    print("=" * 50 + "\n")
    
    # Check if environment variables are set
    required_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these in your .env file or environment\n")
        return
    
    # Run examples
    await example_list_tables()
    await example_describe_table()
    await example_sql_query()
    
    # Natural language query requires OpenAI API key
    if os.getenv("OPENAI_API_KEY"):
        await example_natural_language_query()
    else:
        print("Skipping natural language examples (OPENAI_API_KEY not set)\n")


if __name__ == "__main__":
    asyncio.run(main())

