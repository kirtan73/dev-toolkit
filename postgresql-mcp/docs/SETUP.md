# Setup Guide

## Quick Setup (Recommended)

The easiest way to set up everything is to use the automated setup script:

```bash
./setup.sh
```

Or using Make:

```bash
make setup
```

This single command will:
1. Clean up any existing containers/volumes
2. Start PostgreSQL container
3. Wait for PostgreSQL to be ready
4. Initialize database and user
5. Verify the MCP server can connect

## Manual Setup

If you prefer to set it up step by step:

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `postgresql-mcp` directory:

```env
# PostgreSQL Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=mydb
POSTGRES_USER=postgres-mcp
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

### 3. Start PostgreSQL (if using Docker)

```bash
docker-compose up -d postgres
```

Wait for PostgreSQL to be ready (about 10 seconds).

### 4. Initialize Database

```bash
python scripts/init_db.py
```

This creates the database and user specified in your `.env` file.

### 5. Start the MCP Server

```bash
python mcp_server.py
```

## Troubleshooting

### Password Authentication Failed

If you see `password authentication failed for user "postgres-mcp"`:

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

Test your connection:

```bash
make test-connection
```

Or:

```bash
python scripts/test_connection.py
```

### PostgreSQL Container Not Starting

Check the logs:

```bash
docker-compose logs postgres
```

## Production Deployment

For production:

1. Use strong passwords
2. Store credentials in a secrets management system (not `.env` files)
3. Use SSL/TLS for database connections
4. Set appropriate connection pool sizes
5. Enable monitoring and logging
6. Use read-only database users where possible
