# API Key Management Guide

This guide explains how to configure and use organization-specific API keys for AI-powered question generation in the Exam Simulator.

## Overview

The Exam Simulator allows **superadmins** and **organization admins** to configure their own OpenAI and Google Gemini API keys. This provides:

- **Cost Control**: Each organization pays for their own AI API usage
- **Flexibility**: Organizations can choose their preferred AI provider
- **Isolation**: API costs are isolated per organization
- **Security**: API keys are masked in the UI (only last 4 characters shown)

## Who Can Manage API Keys?

- **Superadmin** (`admin@example.com`): Can configure API keys for ANY organization
- **Organization Admin**: Can configure API keys ONLY for their own organization
- **Teachers/Students**: Cannot access or modify API keys

## How to Configure API Keys

### Step 1: Access Organization Settings

1. Login as an admin or superadmin
2. Navigate to **Admin** → **Organization Branding** (or visit `/organization-settings`)
3. Scroll down to the **AI API Keys** section

### Step 2: Add Your API Keys

The API Keys section has two fields:

#### OpenAI API Key
- **Format**: Starts with `sk-proj-...`
- **Where to get it**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Usage**: Powers question generation using GPT models

#### Google Gemini API Key
- **Format**: Starts with `AIza...`
- **Where to get it**: [Google AI Studio](https://ai.google.dev/)
- **Usage**: Powers question generation using Gemini models

### Step 3: Save Settings

1. Enter your API key(s) in the password fields
2. Click "Save Organization Settings"
3. You'll see confirmation messages for each key saved

**Note**: You can configure one or both API keys. If you only use Gemini, you only need to add the Gemini key.

## How Organization API Keys Work

### Priority System

When a teacher or admin generates questions, the system uses API keys in this priority:

1. **Organization API Key** (if configured)
2. **Global/Environment API Key** (fallback)

### Example Flow

```
User clicks "Generate Questions"
    ↓
System checks: Does this user's organization have API keys?
    ↓
YES → Use organization's API key
NO  → Use global API key from .env file
```

### Benefits

- **For Organizations**: Full control over AI costs and usage
- **For Superadmin**: Can provide demo accounts without sharing personal API keys
- **For Users**: Seamless experience - no configuration needed

## Security Features

### API Key Masking

API keys are **never displayed in full** in the UI:
- Before saving: Input field is type `password`
- After saving: Only last 4 characters shown (e.g., `****************7a3b`)

### Storage

- API keys are stored in the `organization_settings` table
- Database column: `openai_api_key`, `gemini_api_key`
- **Recommendation for Production**: Encrypt keys at rest using database-level encryption

### Access Control

- Only admins of an organization can view/modify their keys
- Superadmin can view/modify all organizations' keys
- Regular users (teachers/students) cannot access this page

## Getting API Keys

### OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-`)
5. **Important**: Save it immediately - you won't be able to see it again!

**Cost Estimate**:
- GPT-4o Mini: ~$0.10 per 100 questions generated
- Pricing: https://openai.com/api/pricing/

### Google Gemini API Key

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Click "Get API Key"
4. Create a new API key or use existing
5. Copy the key (starts with `AIza`)

**Cost Estimate**:
- Gemini 2.5 Flash: FREE up to 15 requests/minute
- Gemini 2.5 Pro: FREE up to 2 requests/minute
- Pricing: https://ai.google.dev/pricing

## Testing Your API Keys

After configuring your API keys:

1. Login as a teacher or admin in your organization
2. Upload a document
3. Click "Generate Questions"
4. Select question types and click "Generate"
5. If successful, questions will be generated using your organization's API key

### Troubleshooting

**Error: "API call failed"**
- Check that your API key is valid
- Ensure you have credits/quota remaining on your account
- Verify the key is for the correct provider (OpenAI vs Gemini)

**Error: "API key not found"**
- No organization key AND no global key configured
- Solution: Add an API key to organization settings OR set environment variable

**Questions generate but use wrong provider**
- Check user's AI Settings (teachers can select preferred provider)
- Go to Settings → AI Settings and select the correct provider

## Database Migration

If upgrading from a previous version, run the migration:

```bash
venv/bin/python migrate_api_keys.py
```

This adds the `openai_api_key` and `gemini_api_key` columns to the `organization_settings` table.

## Configuration for Different Scenarios

### Scenario 1: Single Organization (Self-Hosted)

Set global API keys in `.env`:
```
OPENAI_API_KEY=sk-proj-your-key-here
GEMINI_API_KEY=AIzayour-key-here
```

No need to configure organization keys - all users will use global keys.

### Scenario 2: Multiple Organizations (SaaS)

Each organization configures their own API keys:
- Organization A: Uses their Gemini key
- Organization B: Uses their OpenAI key
- Organization C: Uses global fallback keys

### Scenario 3: Free Tier + Paid Tier

- Free organizations: Use limited global API keys
- Paid organizations: Configure unlimited personal API keys
- Superadmin controls which organizations can add keys

## API Key Rotation

To rotate (change) an API key:

1. Generate a new key from OpenAI/Google
2. Go to Organization Settings
3. Enter the new key in the password field
4. Click "Save Organization Settings"
5. Old key is immediately replaced
6. Revoke the old key from OpenAI/Google platform

## Cost Management

### Monitoring Usage

**OpenAI:**
- Dashboard: https://platform.openai.com/usage
- View API usage, costs, and set spending limits

**Google Gemini:**
- Console: https://console.cloud.google.com/
- Monitor API calls and quotas

### Setting Limits

**OpenAI:**
- Set hard limits: Organization → Billing → Usage limits
- Get email alerts when approaching limit

**Google:**
- Set quotas in Google Cloud Console
- Configure budget alerts

### Cost Optimization Tips

1. **Use Gemini for Most Tasks**: Free tier is generous
2. **Reserve OpenAI for Complex Documents**: When Gemini struggles
3. **Limit Question Count**: Generate 5-10 questions at a time
4. **Reuse Questions**: Save and reuse generated questions
5. **Monitor Usage**: Check dashboards weekly

## Security Best Practices

### DO ✓
- Rotate API keys every 90 days
- Use separate keys for prod/dev environments
- Monitor API usage for anomalies
- Revoke unused keys immediately
- Use database encryption for production

### DON'T ✗
- Share API keys between organizations
- Commit API keys to git repositories
- Store keys in plain text files
- Use production keys for testing
- Give API dashboard access to untrusted users

## Frequently Asked Questions

### Q: Can I use both OpenAI and Gemini?
**A:** Yes! Configure both keys. Users can select their preferred provider in Settings.

### Q: What if I don't configure any API keys?
**A:** The system will fall back to global API keys from `.env` file. If those aren't set either, question generation will fail.

### Q: Can students see the API keys?
**A:** No. Only organization admins can view (masked) and modify keys.

### Q: Do API keys expire?
**A:** OpenAI keys don't expire unless revoked. Google keys may have quota limits that reset monthly.

### Q: How secure is this?
**A:** Keys are stored in the database. For production, use database-level encryption. Keys are masked in the UI and only accessible to admins.

### Q: Can I set different keys for different teachers?
**A:** No. API keys are organization-wide. All teachers in an organization share the same keys.

### Q: What happens if my API key runs out of credits?
**A:** Question generation will fail with an API error. Users will see an error message. Add credits to your OpenAI/Google account to resume.

### Q: Can the superadmin see my organization's API keys?
**A:** Yes. The superadmin (`admin@example.com`) can view and modify ALL organizations' API keys.

## Technical Implementation

### Database Schema

```sql
-- organization_settings table
openai_api_key VARCHAR(500) NULL  -- Organization's OpenAI API key
gemini_api_key VARCHAR(500) NULL  -- Organization's Gemini API key
```

### Model Methods

```python
# Check if keys are configured
org_settings.has_openai_key()  # Returns True/False
org_settings.has_gemini_key()  # Returns True/False

# Get masked keys for display
org_settings.get_masked_openai_key()  # Returns "****************7a3b"
org_settings.get_masked_gemini_key()  # Returns "****************Xy9z"
```

### Question Generation Flow

```python
# In app.py generate_questions route
if current_user.organization:
    org_settings = db_session.query(OrganizationSettings)\
        .filter_by(organization_name=current_user.organization)\
        .first()

    if org_settings:
        openai_key = org_settings.openai_api_key
        gemini_key = org_settings.gemini_api_key

# Pass to question generator
results = generate_questions_mixed(
    text=document.content,
    openai_api_key=openai_key,  # Organization key or None
    gemini_api_key=gemini_key   # Organization key or None
)
```

## Support

For issues or questions:
- Check error messages in the browser console
- Review API provider dashboards for usage/errors
- Verify API keys are valid and have credits
- Contact system administrator (superadmin)

---

**Last Updated:** October 2024
**Version:** 1.0
**Feature:** Organization-Specific API Keys
