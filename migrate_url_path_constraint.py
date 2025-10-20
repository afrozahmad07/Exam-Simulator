#!/usr/bin/env python3
"""
Migration Script: Remove unique constraint from url_path column

This script removes the unique constraint on the url_path column in the
organization_settings table to allow multiple NULL values.

Issue: Multiple organizations with empty url_path were causing
"Duplicate entry 'None' for key 'ix_organization_settings_url_path'" errors.

The unique constraint is now handled at the application level for non-NULL values.

Run this script after updating models.py to apply the schema change.
"""

import sqlite3
import os
import sys
from datetime import datetime


def migrate_sqlite(db_path='exam_simulator.db'):
    """Migrate SQLite database"""
    print(f"\n{'='*60}")
    print("SQLite Migration: Remove url_path unique constraint")
    print(f"{'='*60}\n")
    print(f"Database: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ Error: Database file '{db_path}' not found")
        return False

    # Backup the database first
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\n📦 Creating backup: {backup_path}")

    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print("✅ Backup created successfully")
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current indexes
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='organization_settings'")
        indexes = cursor.fetchall()

        print("\n📊 Current indexes on organization_settings:")
        for idx in indexes:
            print(f"   {idx[0]}: {idx[1]}")

        # SQLite doesn't have a simple ALTER INDEX command, so we need to:
        # 1. Create a new table with the correct schema
        # 2. Copy data from old table
        # 3. Drop old table
        # 4. Rename new table

        print("\n🔄 Creating new table with corrected schema...")
        cursor.execute("""
            CREATE TABLE organization_settings_new (
                id INTEGER PRIMARY KEY,
                organization_name VARCHAR(255) NOT NULL UNIQUE,
                display_name VARCHAR(255) NOT NULL,
                subdomain VARCHAR(100),
                url_path VARCHAR(100),
                logo_filename VARCHAR(255),
                favicon_filename VARCHAR(255),
                primary_color VARCHAR(7) DEFAULT '#0d6efd',
                secondary_color VARCHAR(7) DEFAULT '#6c757d',
                success_color VARCHAR(7) DEFAULT '#198754',
                danger_color VARCHAR(7) DEFAULT '#dc3545',
                custom_css TEXT,
                custom_footer_html TEXT,
                enable_analytics BOOLEAN DEFAULT 1,
                enable_csv_export BOOLEAN DEFAULT 1,
                enable_pdf_export BOOLEAN DEFAULT 1,
                contact_email VARCHAR(255),
                support_url VARCHAR(500),
                openai_api_key VARCHAR(500),
                gemini_api_key VARCHAR(500),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)

        # Create indexes (without UNIQUE on url_path)
        cursor.execute("CREATE INDEX ix_organization_settings_organization_name ON organization_settings_new (organization_name)")
        cursor.execute("CREATE UNIQUE INDEX ix_organization_settings_subdomain ON organization_settings_new (subdomain)")
        cursor.execute("CREATE INDEX ix_organization_settings_url_path ON organization_settings_new (url_path)")

        print("✅ New table created with corrected indexes")

        # Copy data
        print("📋 Copying data from old table...")
        cursor.execute("""
            INSERT INTO organization_settings_new
            SELECT * FROM organization_settings
        """)

        rows_copied = cursor.rowcount
        print(f"✅ Copied {rows_copied} rows")

        # Drop old table
        print("🗑️  Dropping old table...")
        cursor.execute("DROP TABLE organization_settings")
        print("✅ Old table dropped")

        # Rename new table
        print("✏️  Renaming new table...")
        cursor.execute("ALTER TABLE organization_settings_new RENAME TO organization_settings")
        print("✅ Table renamed")

        # Verify the changes
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='organization_settings'")
        indexes = cursor.fetchall()

        print("\n✅ New indexes on organization_settings:")
        for idx in indexes:
            print(f"   {idx[0]}: {idx[1]}")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        print(f"💾 Backup saved at: {backup_path}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        print(f"💾 Database restored from backup: {backup_path}")
        return False
    finally:
        conn.close()


def migrate_mariadb(host='localhost', port=3306, user='exam_user', password=None, database='exam_simulator'):
    """Migrate MariaDB/MySQL database"""
    try:
        import pymysql
    except ImportError:
        print("❌ pymysql is not installed. Install it with: pip install pymysql")
        return False

    print(f"\n{'='*60}")
    print("MariaDB Migration: Remove url_path unique constraint")
    print(f"{'='*60}\n")
    print(f"Database: {database} on {host}:{port}")

    if not password:
        import getpass
        password = getpass.getpass(f"Enter password for {user}@{host}: ")

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        # Check current indexes
        cursor.execute("""
            SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'organization_settings'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """, (database,))

        indexes = cursor.fetchall()
        print("\n📊 Current indexes:")
        for idx in indexes:
            print(f"   {idx[0]} (unique={not idx[1]}): {idx[2]}")

        # Check if the unique index exists
        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'organization_settings'
            AND INDEX_NAME = 'ix_organization_settings_url_path' AND NON_UNIQUE = 0
        """, (database,))

        has_unique_constraint = cursor.fetchone()[0] > 0

        if has_unique_constraint:
            print("\n🔄 Dropping unique index on url_path...")
            cursor.execute("DROP INDEX ix_organization_settings_url_path ON organization_settings")
            print("✅ Unique index dropped")

            print("🔄 Creating non-unique index on url_path...")
            cursor.execute("CREATE INDEX ix_organization_settings_url_path ON organization_settings (url_path)")
            print("✅ Non-unique index created")
        else:
            print("\n⚠️  Unique constraint not found, checking if we need to drop and recreate...")
            cursor.execute("DROP INDEX IF EXISTS ix_organization_settings_url_path ON organization_settings")
            cursor.execute("CREATE INDEX ix_organization_settings_url_path ON organization_settings (url_path)")
            print("✅ Index recreated without unique constraint")

        # Verify the changes
        cursor.execute("""
            SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME
            FROM INFORMATION_SCHEMA.STATISTICS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'organization_settings'
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """, (database,))

        indexes = cursor.fetchall()
        print("\n✅ New indexes:")
        for idx in indexes:
            print(f"   {idx[0]} (unique={not idx[1]}): {idx[2]}")

        conn.commit()
        print("\n✅ Migration completed successfully!")
        return True

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Remove url_path Unique Constraint")
    print("=" * 60)
    print("\nThis migration removes the unique constraint on the url_path column")
    print("to allow multiple NULL values. Uniqueness is now enforced at the")
    print("application level for non-NULL values only.")
    print("\nSelect database type:")
    print("1. SQLite (default)")
    print("2. MariaDB/MySQL")

    choice = input("\nEnter choice (1 or 2, default=1): ").strip() or "1"

    if choice == "1":
        db_path = input("Enter SQLite database path (default=exam_simulator.db): ").strip() or "exam_simulator.db"
        success = migrate_sqlite(db_path)
    elif choice == "2":
        print("\nMariaDB/MySQL Configuration:")
        host = input("Host (default=localhost): ").strip() or "localhost"
        port = input("Port (default=3306): ").strip() or "3306"
        user = input("User (default=exam_user): ").strip() or "exam_user"
        database = input("Database (default=exam_simulator): ").strip() or "exam_simulator"

        success = migrate_mariadb(
            host=host,
            port=int(port),
            user=user,
            database=database
        )
    else:
        print("Invalid choice")
        sys.exit(1)

    sys.exit(0 if success else 1)
