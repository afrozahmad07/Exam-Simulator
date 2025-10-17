#!/usr/bin/env python3
"""
Create Superadmin User

This script creates the superadmin user (admin@example.com) who can see
everything across all organizations.

Usage: python create_superadmin.py
"""

import os
from models import User, get_engine, get_session, create_all_tables

def create_superadmin():
    """Create or update the superadmin user"""
    print("=" * 70)
    print("🔐 CREATING SUPERADMIN USER")
    print("=" * 70)

    # Initialize database
    db_url = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')
    engine = get_engine(db_url)
    create_all_tables(engine)
    session = get_session(engine)

    try:
        # Check if superadmin already exists
        superadmin = session.query(User).filter_by(email='admin@example.com').first()

        if superadmin:
            print("\n⚠️  Superadmin user already exists!")
            print(f"   Email: {superadmin.email}")
            print(f"   Name: {superadmin.name}")
            print(f"   Role: {superadmin.role}")
            print(f"   Organization: {superadmin.organization or 'None'}")

            # Update to superadmin role if needed
            if superadmin.role != 'superadmin':
                print(f"\n🔧 Updating role from '{superadmin.role}' to 'superadmin'...")
                superadmin.role = 'superadmin'
                session.commit()
                print("   ✓ Role updated to superadmin")
        else:
            print("\n✨ Creating new superadmin user...")

            # Create superadmin
            superadmin = User(
                email='admin@example.com',
                name='Super Admin',
                organization=None,  # No organization - sees everything
                role='superadmin'
            )
            superadmin.set_password('admin123')  # Default password

            session.add(superadmin)
            session.commit()

            print("   ✓ Superadmin user created successfully!")

        print("\n" + "=" * 70)
        print("✅ SUPERADMIN SETUP COMPLETE")
        print("=" * 70)
        print("\n🔑 SUPERADMIN LOGIN CREDENTIALS:")
        print("   📧 Email: admin@example.com")
        print("   🔒 Password: admin123")
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("\n💡 SUPERADMIN CAPABILITIES:")
        print("   • View ALL users across ALL organizations")
        print("   • View ALL documents from ALL organizations")
        print("   • View ALL questions from ALL organizations")
        print("   • Manage users in ANY organization")
        print("   • Create other superadmins")
        print("   • Full system access")
        print("\n" + "=" * 70)

        return True

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


if __name__ == '__main__':
    create_superadmin()
