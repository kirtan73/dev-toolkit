"""
Initialize PostgreSQL database and user.
Creates the database and user if they don't exist, using credentials from .env file.
"""

import sys
import asyncio
import asyncpg
from pathlib import Path
import structlog

# Add parent directory to path to import postgresql_mcp
sys.path.insert(0, str(Path(__file__).parent.parent))

from postgresql_mcp.config import settings

logger = structlog.get_logger(__name__)


async def init_database():
    """Initialize PostgreSQL database and user."""
    try:
        # Connect to default 'postgres' database to create our database
        logger.info("Connecting to PostgreSQL server to initialize database")
        
        # Extract connection details from settings
        host = settings.postgres_host
        port = settings.postgres_port
        db_name = settings.postgres_db
        user = settings.postgres_user
        password = settings.postgres_password
        
        # For Docker PostgreSQL, POSTGRES_PASSWORD is the superuser password
        # We need to connect as 'postgres' superuser to create our custom user
        # Try to use POSTGRES_PASSWORD as the superuser password
        superuser_password = password  # Use the password from .env as superuser password
        superuser = "postgres"  # Default superuser in PostgreSQL Docker images
        
        # Try connecting as postgres superuser first
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=superuser,
                password=superuser_password,
                database="postgres"  # Connect to default database
            )
            logger.info("Connected as postgres superuser")
        except Exception as e:
            logger.warning(
                "Failed to connect as postgres superuser, trying with provided user",
                error=str(e)
            )
            # If that fails, try with the provided user (in case it's already the superuser)
            try:
                conn = await asyncpg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database="postgres"
                )
                superuser = user  # Use provided user as superuser
                logger.info(f"Connected as {superuser}")
            except Exception as e2:
                logger.error("Failed to connect to PostgreSQL", error=str(e2))
                print(f"Error: Could not connect to PostgreSQL server.")
                print(f"Tried connecting as:")
                print(f"  1. User 'postgres' with password from POSTGRES_PASSWORD")
                print(f"  2. User '{user}' with password from POSTGRES_PASSWORD")
                print(f"\nMake sure:")
                print(f"  - PostgreSQL is running")
                print(f"  - POSTGRES_PASSWORD in .env matches the postgres superuser password")
                print(f"  - If using Docker, POSTGRES_PASSWORD should be set in docker-compose.yml")
                sys.exit(1)
        
        try:
            # Check if user exists, create if not
            logger.info("Checking if user exists", user=user)
            user_exists = await conn.fetchval(
                "SELECT 1 FROM pg_roles WHERE rolname = $1",
                user
            )
            
            # Drop user if exists to ensure clean creation with correct password
            if user_exists:
                logger.info("User already exists, dropping to recreate with correct password", user=user)
                try:
                    # Drop the user (CASCADE to handle any dependencies)
                    await conn.execute(f'DROP USER IF EXISTS "{user}" CASCADE')
                    logger.info("Old user dropped", user=user)
                except Exception as e:
                    logger.warning("Could not drop existing user, will try to update password", error=str(e))
            
            # Create user with password
            # Note: CREATE USER doesn't support parameterized queries, so we need to escape the password
            # We'll use asyncpg's connection.escape_string() equivalent approach
            logger.info("Creating user", user=user)
            
            # Properly escape the password for SQL
            # Replace single quotes with doubled single quotes for SQL escaping
            escaped_password = password.replace("'", "''")
            # Also escape backslashes
            escaped_password = escaped_password.replace("\\", "\\\\")
            
            await conn.execute(
                f'CREATE USER "{user}" WITH PASSWORD \'{escaped_password}\''
            )
            logger.info("User created successfully", user=user)
            
            # Check if database exists, create if not
            logger.info("Checking if database exists", database=db_name)
            db_exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                db_name
            )
            
            if not db_exists:
                logger.info("Creating database", database=db_name)
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info("Database created successfully", database=db_name)
            else:
                logger.info("Database already exists", database=db_name)
            
            # Grant privileges
            logger.info("Granting privileges", user=user, database=db_name)
            try:
                # Grant all privileges on the database to the user (use quoted identifiers)
                await conn.execute(
                    f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO "{user}"'
                )
                
                # Connect to the new database to grant schema privileges
                await conn.close()
                conn = await asyncpg.connect(
                    host=host,
                    port=port,
                    user=default_user,
                    password=superuser_password,
                    database=db_name
                )
                
                # Grant privileges on the public schema (use quoted identifiers)
                await conn.execute(f'GRANT ALL ON SCHEMA public TO "{user}"')
                await conn.execute(f'GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{user}"')
                await conn.execute(f'GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{user}"')
                await conn.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{user}"')
                await conn.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{user}"')
                
                logger.info("Privileges granted successfully")
            except Exception as e:
                logger.warning("Could not grant all privileges (may not be necessary)", error=str(e))
            
            await conn.close()
            
            # Verify the user can connect with the password
            logger.info("Verifying user can connect", user=user)
            try:
                test_conn = await asyncpg.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=db_name
                )
                await test_conn.close()
                logger.info("User connection verified successfully")
                print(f"✓ Verified: User '{user}' can connect to database '{db_name}'")
            except Exception as e:
                logger.error("Failed to verify user connection", error=str(e))
                print(f"⚠️  Warning: Could not verify user connection: {e}")
                print(f"   Please check that the password is correct in your .env file")
            
            logger.info("Database initialization completed successfully")
            print(f"✓ Database '{db_name}' and user '{user}' initialized successfully!")
            print(f"✓ You can now connect using:")
            print(f"  Host: {host}")
            print(f"  Port: {port}")
            print(f"  Database: {db_name}")
            print(f"  User: {user}")
            
        except Exception as e:
            await conn.close()
            logger.error("Error during database initialization", error=str(e))
            print(f"Error: {e}")
            sys.exit(1)
            
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        print(f"Error: {e}")
        sys.exit(1)


async def main():
    """Main entry point."""
    print("PostgreSQL Database Initialization Script")
    print("=" * 50)
    print()
    
    # Display configuration
    print("Configuration:")
    print(f"  Host: {settings.postgres_host}")
    print(f"  Port: {settings.postgres_port}")
    print(f"  Database: {settings.postgres_db}")
    print(f"  User: {settings.postgres_user}")
    print()
    
    await init_database()


if __name__ == "__main__":
    asyncio.run(main())

