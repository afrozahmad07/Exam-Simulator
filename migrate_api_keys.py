#!/usr/bin/env python3
"""
Database migration script to add API key columns to organization_settings table
"""

import sqlite3
import os


def migrate_database():
    """Add API key columns to organization_settings table"""
    db_path = 'exam_simulator.db'

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=" * 70)
        print("🔧 MIGRATING DATABASE: Adding API Key Columns")
        print("=" * 70)

        # Check if organization_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='organization_settings'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("\n⚠️  organization_settings table does not exist")
            print("   Creating organization_settings table with API key columns...")

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
                    openai_api_key VARCHAR(500),
                    gemini_api_key VARCHAR(500),
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX idx_organization_name ON organization_settings(organization_name)")
            cursor.execute("CREATE INDEX idx_subdomain ON organization_settings(subdomain)")
            cursor.execute("CREATE INDEX idx_url_path ON organization_settings(url_path)")

            conn.commit()
            print("   ✓ organization_settings table created with API key columns")

        else:
            # Table exists, check if API key columns exist
            print("\n📋 Checking organization_settings table...")
            cursor.execute("PRAGMA table_info(organization_settings)")
            columns = [column[1] for column in cursor.fetchall()]

            migrations = []

            if 'openai_api_key' not in columns:
                migrations.append(('openai_api_key', "ALTER TABLE organization_settings ADD COLUMN openai_api_key VARCHAR(500)"))

            if 'gemini_api_key' not in columns:
                migrations.append(('gemini_api_key', "ALTER TABLE organization_settings ADD COLUMN gemini_api_key VARCHAR(500)"))

            if not migrations:
                print("   ✓ All API key columns already exist")
            else:
                for column_name, sql in migrations:
                    print(f"   Adding {column_name} column...")
                    cursor.execute(sql)
                    conn.commit()
                    print(f"   ✓ {column_name} column added")

        conn.close()
        print("\n" + "=" * 70)
        print("✅ DATABASE MIGRATION COMPLETE!")
        print("=" * 70)
        print("\n📊 API Key Columns Added:")
        print("   • openai_api_key (VARCHAR 500) - Stores OpenAI API key")
        print("   • gemini_api_key (VARCHAR 500) - Stores Gemini API key")
        print("\n🔒 SECURITY NOTES:")
        print("   • API keys are stored in plain text in the database")
        print("   • For production, consider encrypting keys at rest")
        print("   • Keys are masked in the UI (only last 4 chars shown)")
        print("   • Only organization admins can view/modify their org's keys")
        print("   • Superadmin can view/modify all organizations' keys")
        print("\n" + "=" * 70)

        return True

    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    migrate_database()
