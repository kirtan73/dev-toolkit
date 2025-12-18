#!/usr/bin/env python3
"""
Test PostgreSQL connection with different credentials.
Helps debug connection issues.
"""

import sys
import asyncio
import asyncpg
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from postgresql_mcp.config import settings
except ImportError as e:
    print(f"Error importing settings: {e}")
    print("Make sure you're running from the project root and .env file exists")
    sys.exit(1)


async def test_connection(host, port, user, password, database="postgres"):
    """Test a PostgreSQL connection."""
    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=5
        )
        await conn.close()
        return True, None
    except Exception as e:
        return False, str(e)


async def main():
    """Test various connection combinations."""
    print("PostgreSQL Connection Tester")
    print("=" * 50)
    print()
    print(f"Host: {settings.postgres_host}")
    print(f"Port: {settings.postgres_port}")
    print(f"Target DB: {settings.postgres_db}")
    print(f"Target User: {settings.postgres_user}")
    print(f"Password length: {len(settings.postgres_password)} characters")
    print()
    
    host = settings.postgres_host
    port = settings.postgres_port
    password = settings.postgres_password
    
    # Test 1: Connect as postgres superuser
    print("Test 1: Connecting as 'postgres' superuser...")
    success, error = await test_connection(host, port, "postgres", password)
    if success:
        print("✓ Successfully connected as 'postgres' superuser")
    else:
        print(f"✗ Failed: {error}")
    print()
    
    # Test 2: Connect as target user
    print(f"Test 2: Connecting as '{settings.postgres_user}' user...")
    success, error = await test_connection(host, port, settings.postgres_user, password)
    if success:
        print(f"✓ Successfully connected as '{settings.postgres_user}'")
    else:
        print(f"✗ Failed: {error}")
    print()
    
    # Test 3: Connect to target database as postgres
    print(f"Test 3: Connecting to database '{settings.postgres_db}' as 'postgres'...")
    success, error = await test_connection(host, port, "postgres", password, settings.postgres_db)
    if success:
        print(f"✓ Successfully connected to '{settings.postgres_db}' as 'postgres'")
    else:
        print(f"✗ Failed: {error}")
    print()
    
    # Recommendations
    print("Recommendations:")
    print("-" * 50)
    
    # Check if postgres connection works
    success, _ = await test_connection(host, port, "postgres", password)
    if not success:
        print("⚠️  Cannot connect as 'postgres' superuser.")
        print("   This usually means:")
        print("   1. The PostgreSQL volume was initialized with a different password")
        print("   2. Solution: Reset the database volume:")
        print("      ./scripts/reset_db.sh")
        print("      OR")
        print("      docker-compose down -v postgres")
        print("      docker-compose up -d postgres")
        print("      sleep 10")
        print("      python scripts/init_db.py")
    else:
        success, _ = await test_connection(host, port, settings.postgres_user, password)
        if not success:
            print("✓ Can connect as 'postgres' superuser")
            print("⚠️  Cannot connect as target user (this is expected before initialization)")
            print("   Run the initialization script:")
            print("   python scripts/init_db.py")
        else:
            print("✓ All connections successful!")
            print("   Your database is properly configured.")


if __name__ == "__main__":
    asyncio.run(main())

