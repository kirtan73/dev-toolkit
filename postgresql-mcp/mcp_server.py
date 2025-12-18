"""
MCP Server implementation for PostgreSQL database queries.
Provides natural language to SQL conversion and read-only query execution.
"""

import asyncio
import json
import sys
from typing import Any, Sequence
import structlog

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from postgresql_mcp.config import settings
from postgresql_mcp.db_pool import db_pool
from postgresql_mcp.sql_validator import SQLValidator
from postgresql_mcp.nl_to_sql import nl_to_sql_converter

# Configure structured logging to stderr (stdout is used for MCP protocol)
import sys
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)
logger = structlog.get_logger(__name__)

# Create MCP server instance
server = Server("postgresql-mcp")


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available database resources."""
    try:
        # Get list of tables as resources
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """
        tables = await db_pool.fetch(tables_query)
        
        resources = [
            Resource(
                uri=f"postgresql://table/{table['table_name']}",
                name=f"Table: {table['table_name']}",
                description=f"PostgreSQL table: {table['table_name']}",
                mimeType="application/json"
            )
            for table in tables
        ]
        
        return resources
    except Exception as e:
        logger.error("Error listing resources", error=str(e))
        return []


@server.read_resource()
async def read_resource(uri: str) -> list[TextContent]:
    """Get resource content (table schema information)."""
    try:
        if not uri.startswith("postgresql://table/"):
            raise ValueError(f"Invalid resource URI: {uri}")
        
        table_name = uri.replace("postgresql://table/", "")
        
        # Get table schema
        columns_query = """
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position;
        """
        columns = await db_pool.fetch(columns_query, table_name)
        
        schema_info = {
            "table": table_name,
            "columns": [
                {
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "nullable": col["is_nullable"] == "YES",
                    "default": col["column_default"]
                }
                for col in columns
            ]
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(schema_info, indent=2)
        )]
    except Exception as e:
        logger.error("Error reading resource", uri=uri, error=str(e))
        raise


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools (query operations)."""
    return [
        Tool(
            name="query_database",
            description=(
                "Execute a SQL SELECT query on the PostgreSQL database. "
                "Only read operations (SELECT) are allowed. "
                "Returns query results as JSON."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="natural_language_query",
            description=(
                "Query the database using natural language. "
                "Converts natural language to SQL and executes it. "
                "Only read operations are supported."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the database"
                    }
                },
                "required": ["question"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database schema.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="describe_table",
            description="Get schema information for a specific table.",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Execute a tool (query operation)."""
    try:
        if name == "query_database":
            query = arguments.get("query")
            if not query:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Query parameter is required"}, indent=2)
                )]
            
            # Validate query
            is_valid, error_msg = SQLValidator.validate_read_only(query)
            if not is_valid:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": error_msg}, indent=2)
                )]
            
            # Execute query
            results = await db_pool.fetch(query)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "row_count": len(results),
                    "data": results
                }, indent=2, default=str)
            )]
        
        elif name == "natural_language_query":
            question = arguments.get("question")
            if not question:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Question parameter is required"}, indent=2)
                )]
            
            # Convert natural language to SQL
            conversion_result = await nl_to_sql_converter.convert_to_sql(question)
            
            if conversion_result["error"]:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": conversion_result["error"],
                        "question": question
                    }, indent=2)
                )]
            
            sql_query = conversion_result["sql"]
            
            # Execute the SQL query
            results = await db_pool.fetch(sql_query)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "question": question,
                    "sql": sql_query,
                    "explanation": conversion_result["explanation"],
                    "row_count": len(results),
                    "data": results
                }, indent=2, default=str)
            )]
        
        elif name == "list_tables":
            tables_query = """
                SELECT 
                    table_name,
                    (SELECT COUNT(*) 
                     FROM information_schema.columns 
                     WHERE table_schema = 'public' 
                     AND table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
            tables = await db_pool.fetch(tables_query)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "tables": tables
                }, indent=2)
            )]
        
        elif name == "describe_table":
            table_name = arguments.get("table_name")
            if not table_name:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "table_name parameter is required"}, indent=2)
                )]
            
            columns_query = """
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position;
            """
            columns = await db_pool.fetch(columns_query, table_name)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "table": table_name,
                    "columns": columns
                }, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
    
    except Exception as e:
        logger.error("Error executing tool", tool=name, error=str(e), error_type=type(e).__name__)
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }, indent=2)
        )]


async def main():
    """Main entry point for the MCP server."""
    # Initialize database pool
    logger.info("Initializing database connection pool")
    await db_pool.initialize()
    
    # Health check
    if not await db_pool.health_check():
        logger.error("Database health check failed")
        sys.exit(1)
    
    logger.info("Database connection pool initialized successfully")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())

