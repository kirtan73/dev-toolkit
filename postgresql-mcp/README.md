# PostgreSQL MCP Server & Client

A **Model Context Protocol (MCP)** server and client for querying PostgreSQL databases using natural language. This implementation supports **read-only operations only**, ensuring data safety while providing intuitive database interaction.

## Features

- 🔍 **Natural Language Queries**: Convert plain English questions to SQL queries using OpenAI
- 🔒 **Read-Only Security**: Strict validation ensures only SELECT queries are executed
- 🚀 **Production-Ready**: Connection pooling, error handling, structured logging, and health checks
- 📊 **Multiple Output Formats**: JSON and table-formatted results
- 🐳 **Docker Support**: Easy deployment with Docker and Docker Compose
- 📈 **Scalable**: Built with async/await for high performance
- 🔧 **Schema Awareness**: Automatically discovers and uses database schema for accurate SQL generation

## Architecture

```
┌─────────────────┐
│   MCP Client    │  ← Natural Language Questions
└────────┬────────┘
         │ MCP Protocol (stdio)
         ▼
┌─────────────────┐
│   MCP Server    │
│  ┌───────────┐  │
│  │ NL → SQL  │  │  ← OpenAI API (optional)
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │ Validator │  │  ← SQL Security Check
│  └─────┬─────┘  │
│        │        │
└────────┼────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │  ← Read-Only Queries Only
└─────────────────┘
```

## Project Structure

```
postgresql-mcp/
├── postgresql_mcp/          # Core package modules
│   ├── __init__.py
│   ├── config.py            # Configuration management
│   ├── db_pool.py           # Database connection pool
│   ├── sql_validator.py     # SQL security validation
│   └── nl_to_sql.py         # Natural language to SQL conversion
├── scripts/                  # Utility scripts
│   ├── init_db.py           # Database initialization
│   ├── example_usage.py     # Usage examples
│   └── test_connection.py   # Connection testing
├── mcp_server.py            # MCP server entry point
├── mcp_client.py            # MCP client entry point
├── setup.sh                 # Automated setup script
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── Makefile
└── README.md
```

## Quick Setup

**One command to set up everything:**

```bash
./setup.sh
```

Or using Make:

```bash
make setup
```

This will:
1. Clean up any existing containers/volumes
2. Start PostgreSQL container
3. Wait for PostgreSQL to be ready
4. Initialize database and user
5. Verify the MCP server can connect

### Manual Database Initialization

If you only want to initialize the database (PostgreSQL must already be running):

```bash
python scripts/init_db.py
```

Or:

```bash
make init-db
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database (local or remote)
- OpenAI API key (for natural language queries)

### Local Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd postgresql-mcp
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Set up environment variables:**
   Create a `.env` file with your configuration:

   ```env
   # PostgreSQL Database Configuration
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432
   POSTGRES_DB=mydb
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_SSL_MODE=prefer
   
   # Connection Pool Settings
   POSTGRES_MIN_POOL_SIZE=5
   POSTGRES_MAX_POOL_SIZE=20
   
   # OpenAI API Configuration (required for natural language queries)
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o-mini
   
   # Server Configuration
   LOG_LEVEL=INFO
   ```

   **Important:** `POSTGRES_PASSWORD` is used for both:
   - The `postgres` superuser (in Docker)
   - Your custom user (`POSTGRES_USER`)

## Usage

### Running the MCP Server

The MCP server communicates via stdio (standard input/output), which is the standard for MCP protocol:

```bash
python mcp_server.py
```

The server will:
1. Initialize the database connection pool
2. Perform a health check
3. Wait for MCP protocol messages on stdio

### Using the MCP Client

The client provides a command-line interface for interacting with the server:

#### Natural Language Query

```bash
python mcp_client.py query "How many users are in the database?"
```

```bash
python mcp_client.py query "Show me the top 10 customers by total orders" --format table
```

#### Direct SQL Query

```bash
python mcp_client.py sql "SELECT COUNT(*) FROM users"
```

#### List Tables

```bash
python mcp_client.py tables
```

#### Describe Table Schema

```bash
python mcp_client.py describe users
```

#### List Resources

```bash
python mcp_client.py resources
```

## Database Setup

### Quick Setup (Recommended)

Use the automated setup script:

```bash
./setup.sh
```

This single command will:
1. Clean up any existing containers/volumes
2. Start PostgreSQL container
3. Wait for PostgreSQL to be ready
4. Initialize database and user
5. Verify the MCP server can connect

### Manual Setup

If you prefer to set it up step by step:

1. **Start PostgreSQL** (if using Docker):
   ```bash
   docker-compose up -d postgres
   ```
   Wait for PostgreSQL to be ready (about 10 seconds).

2. **Initialize Database:**
   ```bash
   python scripts/init_db.py
   ```
   This creates the database and user specified in your `.env` file.

### How Database Initialization Works

1. **Docker PostgreSQL Container:**
   - Uses `POSTGRES_PASSWORD` as the password for the `postgres` superuser
   - The container creates the `postgres` superuser automatically

2. **Initialization Script:**
   - Connects as the `postgres` superuser using `POSTGRES_PASSWORD`
   - Drops and recreates your custom user (`POSTGRES_USER`) to ensure correct password
   - Creates your database (`POSTGRES_DB`) if it doesn't exist
   - Grants all necessary privileges to your custom user

3. **Application Connection:**
   - The MCP server connects using `POSTGRES_USER` and `POSTGRES_PASSWORD`
   - These credentials are stored in your `.env` file

## Docker Deployment

### Using Docker Compose (Recommended)

1. **Set up environment variables in `.env` file:**
   ```env
   POSTGRES_HOST=postgres
   POSTGRES_DB=your_database
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   OPENAI_API_KEY=your_api_key
   ```

2. **Run setup:**
   ```bash
   ./setup.sh
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

   This will start both the MCP server and PostgreSQL database container.

### Using Docker Directly

1. **Build the image:**
   ```bash
   docker build -t postgresql-mcp .
   ```

2. **Run the container:**
   ```bash
   docker run -it --rm \
     -e POSTGRES_HOST=your_host \
     -e POSTGRES_DB=your_db \
     -e POSTGRES_USER=your_user \
     -e POSTGRES_PASSWORD=your_password \
     -e OPENAI_API_KEY=your_key \
     postgresql-mcp
   ```

## System Architecture

### Core Modules

1. **`config.py`** - Configuration Management
   - Loads settings from environment variables
   - Provides PostgreSQL DSN construction
   - Manages connection pool settings
   - Handles OpenAI API configuration

2. **`db_pool.py`** - Database Connection Pool
   - Manages asyncpg connection pool
   - Provides context managers for connection acquisition
   - Implements health checks
   - Handles connection lifecycle

3. **`sql_validator.py`** - SQL Security & Validation
   - Validates queries are read-only (SELECT only)
   - Blocks dangerous SQL operations (INSERT, UPDATE, DELETE, etc.)
   - Detects SQL injection patterns
   - Normalizes and sanitizes queries

4. **`nl_to_sql.py`** - Natural Language to SQL Conversion
   - Uses OpenAI API to convert natural language to SQL
   - Fetches database schema for context
   - Validates generated SQL before execution
   - Provides detailed error messages

5. **`mcp_server.py`** - MCP Server Implementation
   - Implements MCP protocol using stdio transport
   - Provides tools: query_database, natural_language_query, list_tables, describe_table
   - Exposes database tables as resources
   - Handles tool execution and error responses

6. **`mcp_client.py`** - MCP Client Implementation
   - Command-line interface for interacting with server
   - Supports natural language and SQL queries
   - Provides table listing and schema inspection
   - Supports multiple output formats (JSON, table)

### Data Flow

```
User Query (Natural Language)
    ↓
MCP Client
    ↓
MCP Protocol (stdio)
    ↓
MCP Server
    ↓
NL → SQL Converter (OpenAI API)
    ↓
SQL Validator (Security Check)
    ↓
Database Connection Pool
    ↓
PostgreSQL Database
    ↓
Results
    ↓
MCP Client (Formatted Output)
```

### Security Architecture

**Read-Only Enforcement:**
1. **Keyword Blocking**: Blocks INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, etc.
2. **Query Structure Validation**: Ensures queries start with SELECT or WITH
3. **Pattern Detection**: Identifies SQL injection attempts
4. **Database User Permissions**: Should use read-only database user in production

**SQL Injection Prevention:**
- Parameterized queries where applicable
- Pattern matching for dangerous constructs
- Query normalization before validation
- Structured error handling to prevent information leakage

## Production Deployment

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_HOST` | PostgreSQL host | `localhost` | Yes |
| `POSTGRES_PORT` | PostgreSQL port | `5432` | No |
| `POSTGRES_DB` | Database name | - | Yes |
| `POSTGRES_USER` | Database user | - | Yes |
| `POSTGRES_PASSWORD` | Database password | - | Yes |
| `POSTGRES_SSL_MODE` | SSL mode | `prefer` | No |
| `POSTGRES_MIN_POOL_SIZE` | Min connection pool size | `5` | No |
| `POSTGRES_MAX_POOL_SIZE` | Max connection pool size | `20` | No |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes (for NL queries) |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o-mini` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Security Considerations

1. **Read-Only Enforcement**: The server validates all SQL queries to ensure only SELECT statements are executed. Write operations (INSERT, UPDATE, DELETE, DROP, etc.) are blocked.

2. **SQL Injection Prevention**: 
   - Parameterized queries are used when possible
   - Dangerous patterns are detected and blocked
   - Query validation ensures safe operations

3. **Database Credentials**: Store credentials securely using environment variables or a secrets management system (e.g., AWS Secrets Manager, HashiCorp Vault).

4. **Network Security**: In production, ensure:
   - Database connections use SSL/TLS
   - The server is behind a firewall
   - Access is restricted to authorized clients only

### Scaling Considerations

- **Connection Pooling**: The server uses `asyncpg` connection pooling. Adjust `POSTGRES_MIN_POOL_SIZE` and `POSTGRES_MAX_POOL_SIZE` based on your workload.

- **Horizontal Scaling**: Deploy multiple server instances behind a load balancer. Each instance maintains its own connection pool.

- **Monitoring**: Implement monitoring for:
  - Connection pool usage
  - Query execution times
  - Error rates
  - API usage (OpenAI)

### Production Checklist

- [ ] Use strong passwords
- [ ] Store credentials in a secrets management system (not `.env` files)
- [ ] Use SSL/TLS for database connections
- [ ] Set appropriate connection pool sizes
- [ ] Enable monitoring and logging
- [ ] Use read-only database users where possible

## API Reference

### Tools (MCP Server)

#### `query_database`
Execute a SQL SELECT query directly.

**Input:**
```json
{
  "query": "SELECT * FROM users LIMIT 10"
}
```

**Output:**
```json
{
  "success": true,
  "row_count": 10,
  "data": [...]
}
```

#### `natural_language_query`
Convert natural language to SQL and execute.

**Input:**
```json
{
  "question": "How many active users do we have?"
}
```

**Output:**
```json
{
  "success": true,
  "question": "How many active users do we have?",
  "sql": "SELECT COUNT(*) FROM users WHERE active = true",
  "explanation": "Converted 'How many active users do we have?' to SQL query",
  "row_count": 1,
  "data": [...]
}
```

#### `list_tables`
List all tables in the database.

**Input:** `{}`

**Output:**
```json
{
  "success": true,
  "tables": [
    {"table_name": "users", "column_count": 5},
    ...
  ]
}
```

#### `describe_table`
Get schema information for a table.

**Input:**
```json
{
  "table_name": "users"
}
```

**Output:**
```json
{
  "success": true,
  "table": "users",
  "columns": [
    {
      "column_name": "id",
      "data_type": "integer",
      "is_nullable": "NO",
      ...
    },
    ...
  ]
}
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

### Type Checking

```bash
mypy .
```

### Testing Connection

```bash
make test-connection
```

Or:

```bash
python scripts/test_connection.py
```

## Troubleshooting

### Password Authentication Failed

If you see `password authentication failed for user "postgres"`:

1. **Reset the database** (this deletes all data):
   ```bash
   ./setup.sh
   ```
   
   Or manually:
   ```bash
   docker-compose down -v postgres
   docker-compose up -d postgres
   sleep 10
   python scripts/init_db.py
   ```

2. **Check your `.env` file** - Make sure `POSTGRES_PASSWORD` matches what was used when the container was created.

3. **Verify the user exists**:
   ```bash
   docker-compose exec postgres psql -U postgres -c "\du"
   ```

### Connection Issues

- Verify PostgreSQL is running and accessible
- Check credentials in `.env` file
- Ensure network connectivity to the database host
- Verify SSL mode settings match your database configuration
- Test connection: `make test-connection`

### Natural Language Query Issues

- Verify OpenAI API key is set correctly
- Check API quota/rate limits
- Ensure database schema information is accessible
- Review logs for detailed error messages

### Performance Issues

- Increase connection pool size if needed
- Monitor query execution times
- Consider adding indexes to frequently queried columns
- Review OpenAI API response times

### PostgreSQL Container Not Starting

Check the logs:

```bash
docker-compose logs postgres
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or contributions, please open an issue on the repository.
