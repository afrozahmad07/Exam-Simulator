#!/usr/bin/env python3
"""
Migration Script: Expand user_answer column to support short answer responses

This script updates the exam_questions table to change the user_answer column
from VARCHAR(10) to TEXT to accommodate longer short answer responses.

Issue: Students were getting "Data too long for column 'user_answer'" errors
when submitting short answer questions with responses longer than 10 characters.

Run this script after updating models.py to apply the schema change.
"""

import sqlite3
import os
import sys
from datetime import datetime


def migrate_sqlite(db_path='exam_simulator.db'):
    """Migrate SQLite database"""
    print(f"\n{'='*60}")
    print("SQLite Migration: Expand user_answer column")
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
        # Check current schema
        cursor.execute("PRAGMA table_info(exam_questions)")
        columns = cursor.fetchall()

        print("\n📊 Current schema for exam_questions:")
        for col in columns:
            if col[1] == 'user_answer':
                print(f"   user_answer: {col[2]} (nullable: {not col[3]})")

        # SQLite doesn't support ALTER COLUMN directly, so we need to:
        # 1. Create a new table with the correct schema
        # 2. Copy data from old table
        # 3. Drop old table
        # 4. Rename new table

        print("\n🔄 Creating new table with expanded schema...")
        cursor.execute("""
            CREATE TABLE exam_questions_new (
                id INTEGER PRIMARY KEY,
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                user_answer TEXT,
                is_correct BOOLEAN,
                time_spent INTEGER,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            )
        """)

        print("✅ New table created")

        # Copy data
        print("📋 Copying data from old table...")
        cursor.execute("""
            INSERT INTO exam_questions_new
            SELECT id, exam_id, question_id, user_answer, is_correct, time_spent, created_at
            FROM exam_questions
        """)

        rows_copied = cursor.rowcount
        print(f"✅ Copied {rows_copied} rows")

        # Drop old table
        print("🗑️  Dropping old table...")
        cursor.execute("DROP TABLE exam_questions")
        print("✅ Old table dropped")

        # Rename new table
        print("✏️  Renaming new table...")
        cursor.execute("ALTER TABLE exam_questions_new RENAME TO exam_questions")
        print("✅ Table renamed")

        # Verify the change
        cursor.execute("PRAGMA table_info(exam_questions)")
        columns = cursor.fetchall()

        print("\n✅ New schema for exam_questions:")
        for col in columns:
            if col[1] == 'user_answer':
                print(f"   user_answer: {col[2]} (nullable: {not col[3]})")

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
    print("MariaDB Migration: Expand user_answer column")
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

        # Check current schema
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'exam_questions' AND COLUMN_NAME = 'user_answer'
        """, (database,))

        result = cursor.fetchone()
        if result:
            print(f"\n📊 Current schema:")
            print(f"   user_answer: {result[1]} (nullable: {result[2]})")

        # Alter the column
        print("\n🔄 Altering user_answer column...")
        cursor.execute("""
            ALTER TABLE exam_questions
            MODIFY COLUMN user_answer TEXT NULL
        """)

        # Verify the change
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'exam_questions' AND COLUMN_NAME = 'user_answer'
        """, (database,))

        result = cursor.fetchone()
        if result:
            print(f"\n✅ New schema:")
            print(f"   user_answer: {result[1]} (nullable: {result[2]})")

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
    import os

    # Check for auto mode (non-interactive) via environment variable
    auto_mode = os.getenv('AUTO_MIGRATE', 'false').lower() == 'true'

    if auto_mode:
        # Auto mode for deployment scripts - use MariaDB with defaults
        print("Running in auto mode (MariaDB with default configuration)...")
        success = migrate_mariadb(
            host='localhost',
            port=3306,
            user='exam_user',
            database='exam_simulator'
        )
        sys.exit(0 if success else 1)

    # Interactive mode
    print("=" * 60)
    print("Database Migration: Expand user_answer Column")
    print("=" * 60)
    print("\nThis migration expands the user_answer column in the exam_questions")
    print("table from VARCHAR(10) to TEXT to support short answer responses.")
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
