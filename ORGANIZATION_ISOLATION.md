# Organization Isolation & Multi-Tenancy Guide

This document explains the organization isolation and multi-tenancy features implemented in the Exam Simulator application.

## Overview

The application now supports **complete organization isolation** with a **superadmin** role that can oversee all organizations. Users within an organization can only see and interact with data from their own organization, while the superadmin has access to everything.

## Key Features

### 1. Organization-Based Data Isolation

Each user belongs to an organization, and all their data is isolated to that organization:

- **Users**: Organization admins can only see users from their organization
- **Documents**: All organization members can access documents uploaded by anyone in their organization
- **Questions**: Organization members see questions from all documents in their organization
- **Exams**: Users only see their own exam results, but admins can see all exams from their organization

### 2. Superadmin Role

The superadmin (`admin@example.com`) has special privileges:

- View **all users** across **all organizations**
- View **all documents** from **all organizations**
- View **all questions** from **all organizations**
- Manage users in **any organization**
- Create other superadmins
- No organization restrictions

### 3. Organization Members Visibility

A new **Members** page allows users within an organization to see each other:

- **Students** can view other students and teachers in their organization
- **Teachers** can view students and other teachers in their organization
- **Admins** can view all members in their organization
- Members are grouped by role (Admins, Teachers, Students)
- Shows statistics like document count and exam count for each member

## Implementation Details

### Database Schema

The `User` model includes:
- `organization` field: Associates users with an organization
- `role` field: Can be 'student', 'teacher', 'admin', or 'superadmin'

```python
class User(Base, UserMixin):
    organization = Column(String(255), nullable=True)
    role = Column(String(50), default='student')

    def is_superadmin(self):
        """Check if user is a superadmin"""
        return self.role == 'superadmin' or self.email == 'admin@example.com'

    def is_org_admin(self):
        """Check if user is an organization admin (but not superadmin)"""
        return self.role == 'admin' and not self.is_superadmin()
```

### Access Control

#### Admin Dashboard (`app.py:1389-1460`)
```python
# Check if user is superadmin or org admin
is_superadmin = current_user.is_superadmin()

if is_superadmin:
    # Superadmin sees everything
    users_query = db_session.query(User)
else:
    # Org admin sees only their organization
    users_query = db_session.query(User).filter_by(organization=current_user.organization)
```

#### Document Access (`app.py:385-407`)
```python
# Students and teachers can see all documents in their organization
if current_user.organization:
    user_documents = db_session.query(Document)\
        .filter_by(organization=current_user.organization)\
        .order_by(Document.created_at.desc())\
        .all()
```

#### Question Bank (`app.py:769-842`)
```python
# Build query - show all questions from organization's documents
if current_user.organization:
    query = db_session.query(Question).join(Document).filter(
        Document.organization == current_user.organization
    )
```

### Role-Based Decorators

```python
@admin_required
def admin_dashboard():
    """Allows both 'admin' and 'superadmin' roles"""
    pass

@superadmin_required
def superadmin_only_function():
    """Only allows 'superadmin' role"""
    pass
```

## Setup Instructions

### 1. Create Superadmin User

Run the provided script to create or update the superadmin user:

```bash
python create_superadmin.py
```

Or with virtual environment:

```bash
venv/bin/python create_superadmin.py
```

**Default Superadmin Credentials:**
- Email: `admin@example.com`
- Password: `admin123`
- Role: `superadmin`
- Organization: None (sees all organizations)

⚠️ **Important:** Change the password after first login!

### 2. Create Demo Organizations

Run the demo data script to create sample organizations with users:

```bash
venv/bin/python demo_data.py
```

This creates 3 organizations:
- **TechCorp** (5 users)
- **HealthEd** (5 users)
- **FinanceAcademy** (5 users)

Each organization has:
- Multiple students
- At least one teacher
- Sample documents and questions
- Fake exam history

**Default Demo Password:** `demo123` for all demo users

### 3. Test Organization Isolation

1. **Login as Superadmin:**
   - Email: `admin@example.com`
   - Should see all users, documents, and questions from all organizations

2. **Login as Organization Admin:**
   - Example: `eve@techcorp.com` (TechCorp admin)
   - Should only see TechCorp users, documents, and questions
   - Cannot see HealthEd or FinanceAcademy data

3. **Login as Student:**
   - Example: `alice@techcorp.com` (TechCorp student)
   - Can see all TechCorp documents
   - Can view TechCorp members
   - Cannot access admin features

## User Roles & Permissions

### Student
- View organization documents
- Generate questions from documents
- Take exams
- View their own results and analytics
- View organization members
- Upload their own documents

### Teacher
- All student permissions
- Upload documents for organization
- Generate questions with custom AI settings
- Upload questions via CSV
- View organization members

### Organization Admin
- All teacher permissions
- Manage users within their organization
- Change roles of organization members (except superadmins)
- View organization-wide statistics
- Configure organization branding
- **Cannot** see users from other organizations
- **Cannot** modify superadmins

### Superadmin
- **All permissions across all organizations**
- View and manage users in any organization
- Create other superadmins
- Access all documents and questions
- Full system control
- No organization restrictions

## Routes & Access

### Organization Members Page
- **URL:** `/members`
- **Access:** All authenticated users with an organization
- **Features:**
  - View all organization members grouped by role
  - See member statistics (documents uploaded, exams taken)
  - Join date for each member

### Admin Dashboard
- **URL:** `/admin`
- **Access:** Admin and Superadmin roles
- **Filtering:**
  - Superadmin: Sees all organizations
  - Org Admin: Sees only their organization

### Admin Users Management
- **URL:** `/admin/users`
- **Access:** Admin and Superadmin roles
- **Filtering:**
  - Superadmin: Can manage users in any organization
  - Org Admin: Can only manage users in their organization

### Admin Documents Management
- **URL:** `/admin/documents`
- **Access:** Admin and Superadmin roles
- **Filtering:**
  - Superadmin: Sees all documents
  - Org Admin: Sees only organization documents

## Security Considerations

### 1. Access Control
- All admin routes check `@admin_required` or `@superadmin_required`
- Database queries are filtered by organization for non-superadmins
- Users cannot access data from other organizations

### 2. Role Restrictions
- Organization admins cannot:
  - View users from other organizations
  - Modify their own role
  - Modify superadmin users
  - Create superadmins (only superadmins can)

### 3. Document Sharing
- Documents are shared organization-wide
- All members can view but only uploader can delete
- This allows teachers to share study materials with students

## Testing Checklist

- [ ] Superadmin can see all users from all organizations
- [ ] Org admin can only see users from their organization
- [ ] Students can view organization members
- [ ] Teachers can view organization members
- [ ] Documents are visible to all organization members
- [ ] Questions are visible to all organization members
- [ ] Org admin cannot modify users from other organizations
- [ ] Org admin cannot modify superadmin users
- [ ] Members page shows correct role grouping
- [ ] Navigation shows Members link only for users with organization

## Troubleshooting

### Issue: User can see data from other organizations
- Check that queries include `.filter_by(organization=current_user.organization)`
- Verify that the user's organization field is set correctly

### Issue: Superadmin can't see all data
- Verify the user has role='superadmin' or email='admin@example.com'
- Check `is_superadmin()` method in models.py

### Issue: Members page not showing
- Ensure user has an organization set
- Check navigation template condition: `{% if current_user.organization %}`

### Issue: Cannot create superadmin
- Run `venv/bin/python create_superadmin.py`
- Verify database connection
- Check that migrations have been run

## Future Enhancements

Potential improvements for organization features:

1. **Teacher Assignment System:** Allow teachers to assign specific exams to students
2. **Organization Invitations:** Allow admins to invite users via email
3. **Organization Settings:** More granular control over features per organization
4. **Student Groups:** Create groups within organizations for class sections
5. **Shared Question Pools:** Allow organizations to share question banks
6. **Organization Analytics:** Dashboard showing organization-wide performance
7. **Custom Domains:** Support for custom domains per organization
8. **SSO Integration:** Single Sign-On for enterprise organizations

## Migration from Single-Tenant

If you have existing data from a single-tenant setup:

1. Run the migration script:
   ```bash
   venv/bin/python migrate_db.py
   ```

2. Assign organizations to existing users:
   ```python
   # Update users to assign organizations
   from models import User, get_engine, get_session
   db_session = get_session(get_engine())

   users = db_session.query(User).filter_by(organization=None).all()
   for user in users:
       user.organization = 'Default Organization'

   db_session.commit()
   ```

3. Create superadmin:
   ```bash
   venv/bin/python create_superadmin.py
   ```

## Support

For issues or questions about organization isolation:
1. Check this documentation
2. Review the code in `app.py` (routes with organization filtering)
3. Review `models.py` for the data model
4. Test with demo data using `demo_data.py`

---

**Last Updated:** October 2024
**Version:** 1.0
