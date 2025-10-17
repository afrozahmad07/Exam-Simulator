#!/usr/bin/env python3
"""Test script to verify superadmin status and API key access"""

from models import User, OrganizationSettings, get_session, get_engine

def test_superadmin():
    db_engine = get_engine()
    db_session = get_session(db_engine)

    try:
        print("=" * 60)
        print("SUPERADMIN STATUS TEST")
        print("=" * 60)

        # Test admin@example.com
        user = db_session.query(User).filter_by(email='admin@example.com').first()

        if not user:
            print("❌ ERROR: admin@example.com NOT FOUND in database!")
            return

        print(f"\n✓ User Found: {user.email}")
        print(f"  - Name: {user.name}")
        print(f"  - Role in DB: {user.role}")
        print(f"  - Organization: {user.organization}")
        print(f"  - is_superadmin(): {user.is_superadmin()}")
        print(f"  - is_org_admin(): {user.is_org_admin()}")

        # Check what should happen in the template
        is_superadmin = user.is_superadmin()
        is_admin = user.role in ['admin', 'superadmin']

        print(f"\n📋 Template Variables:")
        print(f"  - is_superadmin would be: {is_superadmin}")
        print(f"  - is_admin would be: {is_admin}")

        # Check organization settings
        print(f"\n🏢 Organization Settings:")
        all_orgs = db_session.query(OrganizationSettings).all()
        print(f"  - Total organizations with settings: {len(all_orgs)}")

        for org in all_orgs:
            print(f"\n  Organization: {org.display_name} ({org.organization_name})")
            print(f"    - Has OpenAI key: {org.has_openai_key()}")
            print(f"    - Has Gemini key: {org.has_gemini_key()}")
            if org.has_openai_key():
                print(f"    - Masked OpenAI key: {org.get_masked_openai_key()}")
            if org.has_gemini_key():
                print(f"    - Masked Gemini key: {org.get_masked_gemini_key()}")

        # Test what admin dashboard should show
        print(f"\n🎯 Expected Behavior in Admin Dashboard:")
        if is_superadmin:
            print("  ✓ Should see 'Superadmin Mode' section")
            print("  ✓ Should see 'Organization API Keys' card with 'Superadmin' badge")
            print("  ✓ Should see 'Organization Branding' card with 'Superadmin' badge")
            print("  ✓ Can manage API keys for ANY organization")
        else:
            print("  ✗ Would NOT see superadmin sections")
            print("  ✗ Would only see regular admin sections")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

        if is_superadmin:
            print("\n✅ admin@example.com IS configured as superadmin correctly!")
            print("\nIf you're not seeing superadmin UI:")
            print("  1. Try clearing your browser cache")
            print("  2. Try logging out and logging back in")
            print("  3. Make sure you're accessing /admin route")
            print("  4. Check browser console for JavaScript errors")
        else:
            print("\n❌ admin@example.com is NOT properly configured as superadmin!")
            print("   This needs to be fixed in the database.")

    finally:
        db_session.close()

if __name__ == '__main__':
    test_superadmin()
