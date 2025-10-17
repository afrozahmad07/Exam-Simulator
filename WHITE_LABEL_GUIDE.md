# White-Label Customization Guide

This guide explains how to customize the Exam Simulator with your organization's branding.

## Features

### 1. Organization Settings Database Model
- **Location**: `models.py:151-235`
- Stores all white-label settings per organization
- Supports multiple organizations in the same instance

### 2. Customization Options

#### **Basic Information**
- Organization name (unique identifier)
- Display name (shown in UI)
- Subdomain configuration
- URL path configuration

#### **Branding**
- Custom logo upload (PNG, JPG, JPEG, GIF, SVG)
- Favicon support
- Logo appears in navbar and footer

#### **Color Scheme**
- Primary color (navbar, buttons)
- Secondary color
- Success color (green alerts)
- Danger color (red alerts)
- Real-time color preview

#### **Custom Styling**
- Custom CSS injection
- Override any default styles
- Full control over appearance

#### **Custom Footer**
- Custom HTML content
- Organization contact information
- Support links

#### **Feature Toggles**
- Enable/disable Analytics
- Enable/disable CSV export
- Enable/disable PDF export

#### **Contact Information**
- Contact email
- Support URL

## Usage

### For Admins

1. **Access Organization Settings**
   - Login as admin
   - Navigate to Admin > Organization Branding
   - Route: `/organization-settings`

2. **Set Up Organization**
   - If no organization exists, enter organization name
   - Fill in display name
   - Upload logo (optional)

3. **Customize Colors**
   - Use color pickers for primary, secondary, success, and danger colors
   - Colors update automatically

4. **Add Custom CSS** (Optional)
   - Write custom CSS in the Custom CSS field
   - Example:
   ```css
   .navbar {
       box-shadow: 0 2px 4px rgba(0,0,0,0.1);
   }
   .btn-primary {
       border-radius: 20px;
   }
   ```

5. **Configure Access** (Optional)
   - Set subdomain: `myorg` → accessible at myorg.example.com
   - Set URL path: `my-org` → accessible at example.com/org/my-org

6. **Custom Footer** (Optional)
   - Add custom HTML for footer
   - Include social links, legal info, etc.

### Organization Separation

#### **By Subdomain**
- Each organization can have a unique subdomain
- Example: `acme.examdomain.com`
- Configured in Organization Settings

#### **By URL Path**
- Alternative to subdomains
- Example: `examdomain.com/org/acme`
- Access via `/org/{url_path}`

#### **By User Organization**
- Users are linked to organizations via `organization` field
- Settings automatically applied based on user's organization

## How It Works

### Context Processor
**Location**: `app.py:132-168`

The `inject_org_settings()` context processor:
1. Checks if user is authenticated and has organization
2. Loads organization settings from database
3. Falls back to subdomain detection
4. Falls back to URL path detection
5. Makes `org_settings` available to all templates

### Dynamic Theming
**Location**: `templates/base.html:20-28`

1. Organization theme CSS is injected into `<head>`
2. Custom CSS is added after theme CSS
3. Logo replaces default icon in navbar
4. Display name replaces "Exam Simulator"
5. Footer shows organization contact info

### Color System
**Location**: `models.py:197-235`

The `get_theme_css()` method:
- Generates CSS custom properties for Bootstrap
- Overrides navbar background
- Customizes button colors
- Supports color darkening for hover states

## Database Schema

```python
organization_settings
├── id (Primary Key)
├── organization_name (Unique, Indexed)
├── display_name
├── subdomain (Unique, Indexed)
├── url_path (Unique, Indexed)
├── logo_filename
├── favicon_filename
├── primary_color
├── secondary_color
├── success_color
├── danger_color
├── custom_css
├── custom_footer_html
├── enable_analytics
├── enable_csv_export
├── enable_pdf_export
├── contact_email
├── support_url
├── created_at
└── updated_at
```

## File Structure

```
Exam-Simulator/
├── models.py                          # OrganizationSettings model
├── app.py                             # Routes and context processor
├── templates/
│   ├── base.html                      # Dynamic branding integration
│   └── organization_settings.html     # Admin settings UI
└── static/
    └── logos/                         # Uploaded organization logos
```

## API Routes

### `GET/POST /organization-settings`
- **Access**: Admin only
- **Purpose**: Configure organization white-label settings
- **Template**: `organization_settings.html`

## Examples

### Example 1: University Branding
```python
org_settings = OrganizationSettings(
    organization_name="stanford_university",
    display_name="Stanford University",
    subdomain="stanford",
    primary_color="#8C1515",  # Cardinal red
    secondary_color="#2E2D29", # Cool grey
    contact_email="support@stanford.edu",
    support_url="https://support.stanford.edu"
)
```

### Example 2: Corporate Training
```python
org_settings = OrganizationSettings(
    organization_name="acme_corp",
    display_name="ACME Corp Training",
    url_path="acme",
    primary_color="#0066CC",
    logo_filename="acme_logo.png",
    custom_footer_html="<p>© 2024 ACME Corp. Confidential.</p>"
)
```

## Testing

1. Create an admin user
2. Navigate to `/organization-settings`
3. Set up organization details
4. Upload a logo
5. Change colors
6. View the changes throughout the app

## Migration

To add organization settings to existing database:

```python
from models import get_engine, create_all_tables

engine = get_engine('sqlite:///exam_simulator.db')
create_all_tables(engine)
```

This will create the `organization_settings` table without affecting existing data.

## Best Practices

1. **Logo Size**: Use logos with transparent backgrounds, max 200x50px for best results
2. **Color Contrast**: Ensure text is readable on chosen background colors
3. **Custom CSS**: Test thoroughly before deploying
4. **Subdomain Setup**: Requires DNS configuration on server side
5. **Security**: Sanitize custom HTML to prevent XSS attacks (already handled by Jinja2)

## Troubleshooting

**Q: Logo not showing?**
- Check file was uploaded successfully
- Verify logos folder exists: `static/logos/`
- Check file permissions

**Q: Colors not applying?**
- Clear browser cache
- Check CSS specificity
- Verify color format is valid hex (#RRGGBB)

**Q: Subdomain not working?**
- Ensure DNS is configured
- Check server/reverse proxy configuration
- Test with URL path instead

## Future Enhancements

- [ ] Multiple logo support (light/dark themes)
- [ ] Favicon upload
- [ ] Email template customization
- [ ] Multi-language support
- [ ] Theme presets library
- [ ] Export/import organization settings

---

**For support**: Contact your system administrator or refer to the main README.md
