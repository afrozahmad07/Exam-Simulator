#!/usr/bin/env python3
"""
Database Migration Script
Safely updates database schema without losing data.
Works with both SQLite (development) and MariaDB/MySQL (production).
Uses SQLAlchemy to automatically create/update tables.
"""

import os
from dotenv import load_dotenv
from models import Base, get_engine, create_all_tables

def migrate_database():
    """Run database migrations using SQLAlchemy"""
    # Load environment variables
    load_dotenv()

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')

    print("=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    
    # Determine database type
    if 'mysql' in database_url or 'mariadb' in database_url:
        db_type = "MariaDB/MySQL"
    elif 'postgresql' in database_url:
        db_type = "PostgreSQL"
    elif 'sqlite' in database_url:
        db_type = "SQLite"
    else:
        db_type = "Unknown"
    
    print(f"Database type: {db_type}")
    print(f"Connecting to database...")

    try:
        # Create engine
        engine = get_engine(database_url)

        # Test connection
        with engine.connect() as conn:
            print("✓ Database connection successful")

        # Create/update all tables
        # SQLAlchemy's create_all() is safe - it only creates missing tables
        # It does NOT drop or modify existing tables/data
        print("\nUpdating database schema...")
        create_all_tables(engine)

        print("✓ Database schema updated successfully!")
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        print("\nNotes:")
        print("- This operation is safe and non-destructive")
        print("- Only missing tables/columns are created")
        print("- Existing data is preserved")
        print("- For complex schema changes, consider using Alembic")
        print("")

        return True

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that DATABASE_URL is correct in .env")
        print("2. Ensure database server is running")
        print("3. Verify database credentials")
        print("4. Check that database exists (for MySQL/MariaDB)")
        return False

if __name__ == '__main__':
    import sys
    success = migrate_database()
    sys.exit(0 if success else 1)
