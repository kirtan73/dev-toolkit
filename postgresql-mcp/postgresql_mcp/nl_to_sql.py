"""
Natural Language to SQL conversion module.
Uses OpenAI API to convert natural language queries to SQL.
"""

from typing import Optional, Dict, Any
import re
import structlog
from openai import OpenAI
from openai.types.chat import ChatCompletion

from postgresql_mcp.config import settings
from postgresql_mcp.db_pool import db_pool
from postgresql_mcp.sql_validator import SQLValidator

logger = structlog.get_logger(__name__)


class NLToSQLConverter:
    """Converts natural language queries to SQL using OpenAI."""
    
    def __init__(self):
        self.client: Optional[OpenAI] = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
        else:
            logger.warning("OpenAI API key not provided. NL to SQL conversion will be limited.")
    
    async def get_schema_info(self) -> str:
        """Get database schema information to help with SQL generation."""
        try:
            # Get table names
            tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """
            tables = await db_pool.fetch(tables_query)
            table_names = [t['table_name'] for t in tables]
            
            if not table_names:
                return "No tables found in the database."
            
            # Get columns for each table
            schema_info = []
            for table_name in table_names[:10]:  # Limit to first 10 tables for performance
                columns_query = """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position;
                """
                columns = await db_pool.fetch(columns_query, table_name)
                column_info = [
                    f"  {col['column_name']} ({col['data_type']})"
                    for col in columns
                ]
                schema_info.append(f"Table: {table_name}\n" + "\n".join(column_info))
            
            return "\n\n".join(schema_info)
        except Exception as e:
            logger.error("Failed to get schema info", error=str(e))
            return "Unable to retrieve schema information."
    
    async def convert_to_sql(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Convert natural language query to SQL.
        
        Args:
            natural_language_query: Natural language query string
            
        Returns:
            Dictionary with 'sql', 'error', and 'explanation' keys
        """
        if not self.client:
            return {
                'sql': None,
                'error': 'OpenAI API key not configured',
                'explanation': None
            }
        
        try:
            # Get schema information
            schema_info = await self.get_schema_info()
            
            # Create prompt for OpenAI
            system_prompt = """You are a SQL expert that converts natural language questions into PostgreSQL SELECT queries.

Rules:
1. Only generate SELECT queries (read-only operations)
2. Use proper PostgreSQL syntax
3. Do not include any write operations (INSERT, UPDATE, DELETE, DROP, etc.)
4. Use parameterized queries when possible (but return the SQL as a string)
5. Make queries efficient and use appropriate JOINs when needed
6. Return only the SQL query, no explanations in the query itself

Database Schema:
{schema_info}

Return the SQL query only, without markdown formatting or code blocks."""
            
            user_prompt = f"Convert this natural language question to a PostgreSQL SELECT query:\n\n{natural_language_query}"
            
            messages = [
                {"role": "system", "content": system_prompt.format(schema_info=schema_info)},
                {"role": "user", "content": user_prompt}
            ]
            
            logger.info("Converting NL to SQL", query_preview=natural_language_query[:100])
            
            response: ChatCompletion = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=0.1,  # Lower temperature for more consistent SQL generation
                max_tokens=500,
            )
            
            sql_query = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            sql_query = re.sub(r'```sql\n?', '', sql_query)
            sql_query = re.sub(r'```\n?', '', sql_query)
            sql_query = sql_query.strip()
            
            # Validate the generated SQL
            is_valid, error_msg = SQLValidator.validate_read_only(sql_query)
            
            if not is_valid:
                logger.warning(
                    "Generated SQL failed validation",
                    sql=sql_query,
                    error=error_msg
                )
                return {
                    'sql': None,
                    'error': f"Generated SQL is invalid: {error_msg}",
                    'explanation': None
                }
            
            logger.info("Successfully converted NL to SQL", sql_preview=sql_query[:100])
            
            return {
                'sql': sql_query,
                'error': None,
                'explanation': f"Converted '{natural_language_query}' to SQL query"
            }
            
        except Exception as e:
            logger.error("Error converting NL to SQL", error=str(e), error_type=type(e).__name__)
            return {
                'sql': None,
                'error': f"Error converting query: {str(e)}",
                'explanation': None
            }


# Global converter instance
nl_to_sql_converter = NLToSQLConverter()

