#!/bin/bash
# Complete database setup in one command
# This script sets up PostgreSQL and verifies MCP server can connect

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  PostgreSQL MCP - Complete Setup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file with your PostgreSQL credentials."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Set defaults
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
POSTGRES_DB=${POSTGRES_DB:-postgres}
POSTGRES_USER=${POSTGRES_USER:-postgres}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres}

echo "📋 Configuration:"
echo "   Host: $POSTGRES_HOST"
echo "   Port: $POSTGRES_PORT"
echo "   Database: $POSTGRES_DB"
echo "   User: $POSTGRES_USER"
echo ""

# Step 1: Stop and remove existing containers/volumes
echo "🔧 Step 1: Cleaning up existing containers and volumes..."
docker-compose down -v postgres 2>/dev/null || true
echo "   ✓ Cleaned up"

# Step 2: Start PostgreSQL container
echo ""
echo "🚀 Step 2: Starting PostgreSQL container..."
docker-compose up -d postgres
echo "   ✓ Container started"

# Step 3: Wait for PostgreSQL to be ready
echo ""
echo "⏳ Step 3: Waiting for PostgreSQL to initialize (this may take 10-15 seconds)..."
MAX_WAIT=30
WAITED=0
until docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "   ❌ PostgreSQL did not become ready in time"
        exit 1
    fi
    sleep 1
    WAITED=$((WAITED + 1))
    echo -n "."
done
echo ""
echo "   ✓ PostgreSQL is ready"

# Step 4: Initialize database and user
echo ""
echo "📦 Step 4: Initializing database and user..."
if python scripts/init_db.py; then
    echo "   ✓ Database initialized successfully"
else
    echo "   ❌ Database initialization failed"
    exit 1
fi

# Step 5: Verify connection
echo ""
echo "🔍 Step 5: Verifying MCP server can connect..."
if python -c "
import sys
import os
sys.path.insert(0, '.')
os.chdir('.')

from postgresql_mcp.config import settings
from postgresql_mcp.db_pool import db_pool
import asyncio

async def test():
    try:
        print(f'   Testing connection to: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}')
        print(f'   User: {settings.postgres_user}')
        await db_pool.initialize()
        if await db_pool.health_check():
            print('   ✓ Connection successful!')
            await db_pool.close()
            return True
        else:
            print('   ❌ Health check failed')
            await db_pool.close()
            return False
    except Exception as e:
        print(f'   ❌ Connection failed: {e}')
        print(f'   Error type: {type(e).__name__}')
        return False

if not asyncio.run(test()):
    sys.exit(1)
"; then
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ✅ Setup Complete!"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Your database is ready. You can now start the MCP server:"
    echo ""
    echo "  python mcp_server.py"
    echo ""
    echo "Or using Docker:"
    echo "  docker-compose up postgresql-mcp"
    echo ""
else
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ❌ Setup Failed"
    echo "═══════════════════════════════════════════════════════════"
    echo ""
    echo "Connection verification failed. Please check:"
    echo "  1. Your .env file has correct credentials"
    echo "  2. PostgreSQL container is running: docker-compose ps"
    echo "  3. Check logs: docker-compose logs postgres"
    exit 1
fi

