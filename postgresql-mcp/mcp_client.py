"""
MCP Client for interacting with the PostgreSQL MCP Server.
Provides a command-line interface for natural language database queries.
"""

import asyncio
import json
import sys
import argparse
from typing import Any, Optional
import structlog

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger(__name__)


class PostgreSQLMCPClient:
    """Client for interacting with PostgreSQL MCP Server."""
    
    def __init__(self, server_command: list[str]):
        """
        Initialize the MCP client.
        
        Args:
            server_command: Command to start the MCP server (e.g., ["python", "mcp_server.py"])
        """
        self.server_params = StdioServerParameters(
            command=server_command[0],
            args=server_command[1:] if len(server_command) > 1 else [],
            env=None
        )
    
    async def natural_language_query(self, question: str) -> dict[str, Any]:
        """
        Execute a natural language query.
        
        Args:
            question: Natural language question about the database
            
        Returns:
            Query results as dictionary
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "natural_language_query",
                    arguments={"question": question}
                )
                
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
        
        return {"error": "No result received"}
    
    async def sql_query(self, query: str) -> dict[str, Any]:
        """
        Execute a SQL query directly.
        
        Args:
            query: SQL SELECT query
            
        Returns:
            Query results as dictionary
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "query_database",
                    arguments={"query": query}
                )
                
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
        
        return {"error": "No result received"}
    
    async def list_tables(self) -> dict[str, Any]:
        """List all tables in the database."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool("list_tables", arguments={})
                
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
        
        return {"error": "No result received"}
    
    async def describe_table(self, table_name: str) -> dict[str, Any]:
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table to describe
            
        Returns:
            Table schema information
        """
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.call_tool(
                    "describe_table",
                    arguments={"table_name": table_name}
                )
                
                if result.content:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
        
        return {"error": "No result received"}
    
    async def list_resources(self) -> list[dict[str, Any]]:
        """List available database resources."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                result = await session.list_resources()
                
                return [
                    {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description or "",
                        "mimeType": resource.mimeType or ""
                    }
                    for resource in result.resources
                ]


def print_results(results: dict[str, Any], format_output: str = "json"):
    """Print query results in specified format."""
    if format_output == "json":
        print(json.dumps(results, indent=2, default=str))
    elif format_output == "table" and "data" in results:
        data = results["data"]
        if not data:
            print("No results found.")
            return
        
        # Print header
        headers = list(data[0].keys())
        print(" | ".join(headers))
        print("-" * (sum(len(h) for h in headers) + 3 * len(headers)))
        
        # Print rows
        for row in data:
            values = [str(row.get(h, "")) for h in headers]
            print(" | ".join(values))
    else:
        print(json.dumps(results, indent=2, default=str))


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PostgreSQL MCP Client - Query database with natural language"
    )
    parser.add_argument(
        "--server",
        type=str,
        default="python",
        help="Command to run the MCP server (default: python)"
    )
    parser.add_argument(
        "--server-args",
        type=str,
        nargs="*",
        default=["mcp_server.py"],
        help="Arguments for the server command (default: mcp_server.py)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Natural language query
    nl_parser = subparsers.add_parser("query", help="Query database with natural language")
    nl_parser.add_argument("question", help="Natural language question")
    nl_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json)"
    )
    
    # SQL query
    sql_parser = subparsers.add_parser("sql", help="Execute SQL query directly")
    sql_parser.add_argument("query", help="SQL SELECT query")
    sql_parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format (default: json)"
    )
    
    # List tables
    subparsers.add_parser("tables", help="List all tables")
    
    # Describe table
    describe_parser = subparsers.add_parser("describe", help="Describe table schema")
    describe_parser.add_argument("table_name", help="Name of the table")
    
    # List resources
    subparsers.add_parser("resources", help="List available resources")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create client
    server_command = [args.server] + (args.server_args if args.server_args else [])
    client = PostgreSQLMCPClient(server_command)
    
    try:
        if args.command == "query":
            results = await client.natural_language_query(args.question)
            print_results(results, args.format)
        elif args.command == "sql":
            results = await client.sql_query(args.query)
            print_results(results, args.format)
        elif args.command == "tables":
            results = await client.list_tables()
            print_results(results)
        elif args.command == "describe":
            results = await client.describe_table(args.table_name)
            print_results(results)
        elif args.command == "resources":
            results = await client.list_resources()
            print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error("Error executing command", error=str(e), error_type=type(e).__name__)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

