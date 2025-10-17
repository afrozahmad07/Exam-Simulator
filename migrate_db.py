#!/usr/bin/env python3
"""
Database migration script to add missing columns
"""

import sqlite3
import os


def migrate_database():
    """Add missing columns to database tables"""
    db_path = 'exam_simulator.db'

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Migrate users table
        print("Checking users table...")
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]

        user_migrations = [
            ('remember_token', "ALTER TABLE users ADD COLUMN remember_token VARCHAR(255)"),
            ('ai_provider', "ALTER TABLE users ADD COLUMN ai_provider VARCHAR(50) DEFAULT 'gemini'"),
            ('ai_model', "ALTER TABLE users ADD COLUMN ai_model VARCHAR(100) DEFAULT 'gemini-2.5-flash'"),
        ]

        for column_name, sql in user_migrations:
            if column_name not in user_columns:
                print(f"  Adding {column_name} column to users table...")
                cursor.execute(sql)
                conn.commit()
                print(f"  ✓ {column_name} column added")
            else:
                print(f"  ✓ {column_name} column exists")

        # Migrate questions table
        print("\nChecking questions table...")
        cursor.execute("PRAGMA table_info(questions)")
        question_columns = [column[1] for column in cursor.fetchall()]

        migrations = [
            ('question_type', "ALTER TABLE questions ADD COLUMN question_type VARCHAR(20) DEFAULT 'mcq'"),
            ('model_answer', "ALTER TABLE questions ADD COLUMN model_answer TEXT"),
            ('key_points', "ALTER TABLE questions ADD COLUMN key_points JSON"),
            ('status', "ALTER TABLE questions ADD COLUMN status VARCHAR(20) DEFAULT 'pending'"),
            ('created_by', "ALTER TABLE questions ADD COLUMN created_by INTEGER"),
        ]

        for column_name, sql in migrations:
            if column_name not in question_columns:
                print(f"  Adding {column_name} column to questions table...")
                cursor.execute(sql)
                conn.commit()
                print(f"  ✓ {column_name} column added")
            else:
                print(f"  ✓ {column_name} column exists")

        # Update existing MCQ questions to have proper type
        print("\nUpdating existing questions...")
        cursor.execute("UPDATE questions SET question_type = 'mcq', status = 'approved' WHERE question_type IS NULL OR question_type = ''")
        updated = cursor.rowcount
        conn.commit()
        if updated > 0:
            print(f"  ✓ Updated {updated} existing questions")
        else:
            print("  ✓ No questions to update")

        # Fix options_json column to allow NULL values (for True/False and Short Answer questions)
        print("\nFixing options_json column constraints...")
        try:
            # SQLite doesn't support ALTER COLUMN directly, so we need to:
            # 1. Create a new table with the correct schema
            # 2. Copy data from old table
            # 3. Drop old table
            # 4. Rename new table

            # Check if we need to fix the constraint
            cursor.execute("PRAGMA table_info(questions)")
            columns_info = cursor.fetchall()
            options_json_col = [col for col in columns_info if col[1] == 'options_json']

            if options_json_col and options_json_col[0][3] == 1:  # notnull == 1 means NOT NULL
                print("  Recreating questions table to allow NULL in options_json...")

                # Create backup table
                cursor.execute("""
                    CREATE TABLE questions_new (
                        id INTEGER PRIMARY KEY,
                        question_text TEXT NOT NULL,
                        question_type VARCHAR(20) DEFAULT 'mcq',
                        options_json JSON,
                        correct_answer VARCHAR(10),
                        model_answer TEXT,
                        key_points JSON,
                        explanation TEXT,
                        document_id INTEGER NOT NULL,
                        difficulty VARCHAR(20) DEFAULT 'medium',
                        status VARCHAR(20) DEFAULT 'pending',
                        created_by INTEGER,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY (document_id) REFERENCES documents(id),
                        FOREIGN KEY (created_by) REFERENCES users(id)
                    )
                """)

                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO questions_new
                    SELECT id, question_text, question_type, options_json, correct_answer,
                           model_answer, key_points, explanation, document_id, difficulty,
                           status, created_by, created_at
                    FROM questions
                """)

                # Drop old table
                cursor.execute("DROP TABLE questions")

                # Rename new table
                cursor.execute("ALTER TABLE questions_new RENAME TO questions")

                conn.commit()
                print("  ✓ options_json column fixed - now allows NULL")
            else:
                print("  ✓ options_json column already allows NULL")

        except Exception as e:
            print(f"  ⚠ Could not fix options_json constraint: {e}")
            print("  This might not be an issue if your schema is already correct.")

        # Create organization_settings table
        print("\nChecking organization_settings table...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organization_settings'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("  Creating organization_settings table...")
            cursor.execute("""
                CREATE TABLE organization_settings (
                    id INTEGER PRIMARY KEY,
                    organization_name VARCHAR(255) UNIQUE NOT NULL,
                    display_name VARCHAR(255) NOT NULL,
                    subdomain VARCHAR(100) UNIQUE,
                    url_path VARCHAR(100) UNIQUE,
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
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX idx_organization_name ON organization_settings(organization_name)")
            cursor.execute("CREATE INDEX idx_subdomain ON organization_settings(subdomain)")
            cursor.execute("CREATE INDEX idx_url_path ON organization_settings(url_path)")

            conn.commit()
            print("  ✓ organization_settings table created")
        else:
            print("  ✓ organization_settings table already exists")

        conn.close()
        print("\n✅ Database migration complete!")
        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False


if __name__ == '__main__':
    migrate_database()
