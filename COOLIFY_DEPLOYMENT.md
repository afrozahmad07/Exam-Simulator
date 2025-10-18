# Coolify Deployment Guide for Exam Simulator

This guide will help you deploy the Exam Simulator application on Coolify.

## Prerequisites

- Coolify server running (Ubuntu 22.04)
- GitHub repository access
- Domain name (optional, but recommended)

## Quick Deployment Steps

### 1. Connect to Coolify

1. Log in to your Coolify dashboard
2. Navigate to **Projects** > **New Resource**
3. Select **Public Repository**

### 2. Configure Repository

- **Repository URL**: `https://github.com/afrozahmad07/Exam-Simulator.git`
- **Branch**: `main`
- **Build Pack**: Docker (Coolify will auto-detect the Dockerfile)

### 3. Configure Environment Variables

Click on **Environment Variables** and add the following:

#### Required Variables

```bash
# Flask Secret Key (generate a random string)
SECRET_KEY=your-super-secret-random-key-change-this

# Database URL (use SQLite for simple setup or PostgreSQL for production)
DATABASE_URL=sqlite:///exam_simulator.db

# AI API Keys (at least one required for question generation)
OPENAI_API_KEY=sk-your-openai-api-key
# OR
GEMINI_API_KEY=your-gemini-api-key

# Production Settings
FLASK_ENV=production
FLASK_DEBUG=False
```

#### Security Settings (Important for HTTPS)

```bash
REMEMBER_COOKIE_SECURE=True
SESSION_COOKIE_SECURE=True
```

### 4. Configure Port

- **Port**: `8000` (default - Coolify will handle this automatically)

### 5. Configure Persistent Storage (Optional but Recommended)

Add a volume mount for persistent data:

1. Go to **Storage** in your Coolify resource
2. Add a new volume:
   - **Source**: `/var/lib/coolify/volumes/exam-simulator-uploads`
   - **Destination**: `/app/uploads`
   - **Description**: Uploaded documents storage

3. Add database volume (if using SQLite):
   - **Source**: `/var/lib/coolify/volumes/exam-simulator-db`
   - **Destination**: `/app`
   - **Description**: Database storage

### 6. Configure Domain (Optional)

1. Go to **Domains** section
2. Add your domain: `exam.yourdomain.com`
3. Coolify will automatically provision SSL certificate via Let's Encrypt

### 7. Deploy

1. Click **Deploy** button
2. Coolify will:
   - Clone your repository
   - Build the Docker image
   - Start the container
   - Configure reverse proxy
   - Set up SSL certificate

### 8. Initialize Database (First Time Only)

After deployment, run the database initialization:

1. Go to **Terminal** in Coolify
2. Run:
   ```bash
   python init_db.py
   ```

3. Create a superadmin user:
   ```bash
   python create_superadmin.py
   ```
   Follow the prompts to create your admin account.

## Post-Deployment Configuration

### Create First Admin User

1. Visit your deployed application
2. Register a new account
3. Access the database terminal in Coolify
4. Run: `python create_superadmin.py` with your registered email

### Configure Auto-Deployment (Optional)

Enable auto-deployment on git push:

1. Go to **Settings** > **General**
2. Enable **Auto Deploy on Git Push**
3. Coolify will automatically redeploy when you push to GitHub

## Database Options

### SQLite (Simple, Development)

Use for testing or small deployments:
```bash
DATABASE_URL=sqlite:///exam_simulator.db
```

### PostgreSQL (Production Recommended)

1. Create a PostgreSQL database in Coolify
2. Get the connection string
3. Update environment variable:
   ```bash
   DATABASE_URL=postgresql://user:password@postgres-host:5432/exam_db
   ```

## Monitoring & Logs

- **Logs**: Available in Coolify dashboard under **Logs** tab
- **Metrics**: View CPU, memory, and network usage
- **Health Check**: Application has built-in health check endpoint

## Troubleshooting

### Application Won't Start

1. Check logs in Coolify dashboard
2. Verify all environment variables are set
3. Ensure SECRET_KEY is configured
4. Check database connectivity

### Database Errors

1. Run database initialization:
   ```bash
   python init_db.py
   ```
2. Check DATABASE_URL format
3. Verify database permissions

### Upload Issues

1. Ensure uploads volume is mounted correctly
2. Check folder permissions in terminal:
   ```bash
   chmod 755 /app/uploads
   ```

### AI Question Generation Not Working

1. Verify OPENAI_API_KEY or GEMINI_API_KEY is set
2. Check API key validity
3. Review logs for API errors

## Updating the Application

### Manual Update

1. Push changes to GitHub
2. Click **Redeploy** in Coolify dashboard

### Automatic Updates

With auto-deploy enabled, updates happen automatically on git push.

## Backup Recommendations

1. **Database**: Regularly backup your database volume
2. **Uploads**: Backup the uploads volume containing user documents
3. **Environment Variables**: Keep a secure copy of your .env configuration

## Security Best Practices

1. Use strong SECRET_KEY (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
2. Enable HTTPS (automatic with Coolify + domain)
3. Set secure cookie flags to True
4. Regularly update dependencies
5. Keep API keys secure and rotated
6. Use PostgreSQL for production (better than SQLite)

## Performance Optimization

1. Use PostgreSQL instead of SQLite for better concurrent access
2. Configure Gunicorn workers based on CPU cores
3. Enable Coolify's built-in caching
4. Monitor resource usage and scale as needed

## Support & Resources

- **GitHub Repository**: https://github.com/afrozahmad07/Exam-Simulator
- **Coolify Docs**: https://coolify.io/docs
- **Application Docs**: See README.md in repository

## Estimated Deployment Time

- **Initial Setup**: 5-10 minutes
- **Build Time**: 2-3 minutes
- **Total Time to Live**: ~10-15 minutes

## Minimal Resource Requirements

- **CPU**: 1 vCPU
- **RAM**: 512 MB minimum (1 GB recommended)
- **Storage**: 2 GB minimum (depends on uploaded documents)

Enjoy your Exam Simulator deployment on Coolify!
