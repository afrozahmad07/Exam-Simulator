# Flask Exam Simulator - Production Deployment

A comprehensive AI-powered exam simulator with organization management, white-label branding, and multi-tenant support.

## Quick Links

- **Quick Start**: [QUICK_DEPLOYMENT.md](QUICK_DEPLOYMENT.md) - Deploy in 45 minutes
- **Full Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete deployment documentation
- **Dev Workflow**: [LOCAL_DEV_WORKFLOW.md](LOCAL_DEV_WORKFLOW.md) - Local development guide
- **Features**: See below

---

## Features

### Core Features
- 📚 Document upload and text extraction (PDF, DOCX, TXT)
- 🤖 AI-powered question generation (OpenAI GPT-4, Google Gemini)
- ✅ Multiple question types (MCQ, True/False, Short Answer)
- 📝 CSV bulk question import
- ⏱️ Timed exam simulation
- 📊 Detailed analytics and progress tracking
- 📄 PDF result export

### Multi-Organization Support
- 🏢 Organization-based data isolation
- 👥 Role-based access control (Superadmin, Admin, Teacher, Student)
- 🎨 White-label branding per organization
- 🔑 Per-organization API key management

### Security
- 🔒 Secure authentication with Flask-Login
- 👤 Role-based permissions
- 🔐 Password hashing with Werkzeug
- 🛡️ Organization data isolation
- 🌐 HTTPS/SSL support

---

## System Requirements

### Development (Windows PC with WSL)
- Windows 10/11 with WSL2
- Ubuntu 24.04 (in WSL)
- Python 3.11+
- 4GB RAM minimum
- Git

### Production (VPS)
- Rocky Linux 8.10
- 2GB RAM minimum (4GB recommended)
- 20GB disk space minimum
- Python 3.11+
- Virtualmin/Webmin
- Nginx or Apache
- Public IP address
- Domain name

---

## Deployment Options

### Option 1: Quick Deployment (Recommended)
Perfect for experienced users who want to get running quickly.

**Time**: ~45 minutes

See: [QUICK_DEPLOYMENT.md](QUICK_DEPLOYMENT.md)

### Option 2: Detailed Deployment
Step-by-step guide with explanations for each step.

**Time**: ~2 hours (including learning)

See: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Cloudflare DNS                      │
│            examsimulator.afrozahmad.com                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Rocky Linux VPS                       │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Nginx/Apache (Port 80/443)                 │ │
│  │              - SSL Termination                     │ │
│  │              - Static File Serving                 │ │
│  │              - Reverse Proxy                       │ │
│  └──────────────────┬────────────────────────────────┘ │
│                     │                                    │
│                     ▼                                    │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Gunicorn (Port 8000)                       │ │
│  │           - WSGI Server                            │ │
│  │           - Multiple Workers                       │ │
│  └──────────────────┬────────────────────────────────┘ │
│                     │                                    │
│                     ▼                                    │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Flask Application                          │ │
│  │           - app.py                                 │ │
│  │           - models.py                              │ │
│  │           - question_generator.py                  │ │
│  └──────────────────┬────────────────────────────────┘ │
│                     │                                    │
│                     ▼                                    │
│  ┌───────────────────────────────────────────────────┐ │
│  │         SQLite Database                            │ │
│  │         (or PostgreSQL/MySQL)                      │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Exam-Simulator/
├── app.py                          # Main Flask application
├── models.py                       # SQLAlchemy database models
├── utils.py                        # Utility functions
├── question_generator.py           # AI question generation
├── wsgi.py                        # Production WSGI entry point
│
├── requirements.txt               # Development dependencies
├── requirements-production.txt    # Production dependencies
│
├── .env                          # Environment variables (not in git)
├── .env.production               # Production env template
├── gunicorn_config.py            # Gunicorn configuration
│
├── deploy.sh                     # Deployment script
├── setup-systemd.sh              # Systemd setup script
├── update-from-github.sh         # Update script
│
├── nginx-virtualmin-config.conf  # Nginx configuration
├── apache-virtualmin-config.conf # Apache configuration
│
├── DEPLOYMENT_GUIDE.md           # Complete deployment guide
├── LOCAL_DEV_WORKFLOW.md         # Development workflow
├── QUICK_DEPLOYMENT.md           # Quick deployment guide
├── README.md                     # This file
│
├── templates/                    # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── ...
│
├── static/                       # Static assets
│   ├── css/
│   ├── js/
│   ├── images/
│   └── logos/
│
├── uploads/                      # User uploaded files (not in git)
└── venv/                        # Python virtual environment (not in git)
```

---

## Configuration Files

### Environment Variables (.env)

```env
# Flask Configuration
SECRET_KEY=your_secure_random_secret_key
FLASK_ENV=production
FLASK_DEBUG=False

# Database
DATABASE_URL=sqlite:///exam_simulator.db

# AI API Keys (optional - can be set per organization)
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key

# Security
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True

# Domain
DOMAIN=examsimulator.afrozahmad.com
```

### Systemd Service

Located at: `/etc/systemd/system/exam_simulator.service`

Manages the application as a system service with auto-restart on failure.

### Gunicorn Configuration

`gunicorn_config.py` - Configures:
- Worker processes
- Timeouts
- Logging
- Security settings

---

## Development Workflow

### 1. Local Development (WSL Ubuntu)

```bash
# Navigate to project
cd /home/afroz/Exam-Simulator

# Activate virtual environment
source venv/bin/activate

# Run development server
python app.py
```

### 2. Make Changes

Edit files in your preferred editor:
- VS Code with Remote-WSL extension (recommended)
- Vim/Nano in terminal
- Any Windows editor via `\\wsl$\Ubuntu\home\afroz\Exam-Simulator`

### 3. Test Locally

Visit http://localhost:5000

### 4. Commit to Git

```bash
git add .
git commit -m "Description of changes"
git push origin main
```

### 5. Deploy to VPS

```bash
ssh examsim@YOUR_VPS_IP
cd ~/exam-simulator
./update-from-github.sh
```

For detailed workflow, see: [LOCAL_DEV_WORKFLOW.md](LOCAL_DEV_WORKFLOW.md)

---

## User Roles

### Superadmin
- Full system access
- Manage all organizations
- Manage all users
- View all data

### Admin (Organization)
- Manage organization settings
- Manage organization users
- Configure white-label branding
- Set organization API keys
- View organization analytics

### Teacher
- Upload study materials
- Generate questions
- Create exams
- View student results (within organization)
- Configure AI preferences

### Student
- Access study materials
- Take exams
- View own results and analytics
- Track progress

---

## API Integrations

### OpenAI GPT-4
- Advanced question generation
- High-quality explanations
- Multiple question types

### Google Gemini
- Fast question generation (default)
- Cost-effective
- Good quality results

Configuration is per-organization or per-teacher.

---

## Security Considerations

1. **Strong Passwords**: Use strong SECRET_KEY and user passwords
2. **HTTPS Only**: Always use SSL in production
3. **Firewall**: Only open necessary ports (80, 443, 10000)
4. **Regular Updates**: Keep system and dependencies updated
5. **Backups**: Regular database and upload backups
6. **Monitoring**: Monitor logs for suspicious activity
7. **Database**: Use PostgreSQL/MySQL for production (instead of SQLite)
8. **Environment Variables**: Never commit .env to git

---

## Maintenance

### Daily
- Monitor application logs
- Check service status

### Weekly
- Review analytics
- Check disk space
- Review user activity

### Monthly
- Update system packages
- Update Python dependencies
- Review and test backups
- Check SSL certificate expiry

### Backup Strategy

```bash
# Automated daily backup (via cron)
0 2 * * * /home/examsim/backup-exam-simulator.sh

# Manual backup
cd ~/exam-simulator
cp exam_simulator.db backups/exam_simulator_$(date +%Y%m%d).db
tar -czf backups/uploads_$(date +%Y%m%d).tar.gz uploads/
```

---

## Monitoring

### Application Status

```bash
# Service status
sudo systemctl status exam_simulator

# Live logs
sudo journalctl -u exam_simulator -f

# Recent errors
sudo journalctl -u exam_simulator -p err -n 50
```

### System Resources

```bash
# Disk usage
df -h

# Memory usage
free -h

# CPU usage
top

# Process info
htop
```

---

## Troubleshooting

### Common Issues

**502 Bad Gateway**
- Check if Gunicorn is running: `sudo systemctl status exam_simulator`
- Check logs: `sudo journalctl -u exam_simulator -n 50`
- Restart service: `sudo systemctl restart exam_simulator`

**Permission Denied**
- Fix ownership: `sudo chown -R examsim:examsim /home/examsim/exam-simulator`
- Fix .env permissions: `chmod 600 .env`

**Database Locked**
- Using SQLite with high traffic? Upgrade to PostgreSQL
- Restart application: `sudo systemctl restart exam_simulator`

**SSL Certificate Expired**
- Renew: `sudo certbot renew`
- Auto-renewal should be configured by default

For more issues, see: [DEPLOYMENT_GUIDE.md - Troubleshooting](DEPLOYMENT_GUIDE.md#troubleshooting)

---

## Performance Optimization

### For High Traffic

1. **Use PostgreSQL/MySQL** instead of SQLite
2. **Increase Gunicorn workers** in `gunicorn_config.py`
3. **Enable Cloudflare proxy** (orange cloud)
4. **Use Redis** for session storage
5. **Enable database connection pooling**
6. **Implement caching** for static content
7. **Use CDN** for static assets

### Database Migration (SQLite → PostgreSQL)

```bash
# Install PostgreSQL
sudo dnf install postgresql-server postgresql-contrib -y
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Install Python PostgreSQL adapter
pip install psycopg2-binary

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://username:password@localhost/exam_simulator

# Migrate data (use a migration tool or export/import)
```

---

## Support and Documentation

- **Full Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Development Workflow**: [LOCAL_DEV_WORKFLOW.md](LOCAL_DEV_WORKFLOW.md)
- **Quick Deployment**: [QUICK_DEPLOYMENT.md](QUICK_DEPLOYMENT.md)
- **Application Features**: See existing documentation in project
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Virtualmin Docs**: https://www.virtualmin.com/documentation

---

## License

[Your License Here]

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## Changelog

### Version 1.0 (Current)
- Initial production deployment setup
- Multi-organization support
- White-label branding
- AI question generation
- Comprehensive deployment documentation
- Automated update scripts
- Systemd service configuration

---

## Acknowledgments

- Flask framework and contributors
- OpenAI for GPT-4 API
- Google for Gemini API
- Virtualmin project
- Rocky Linux community

---

**Deployed Successfully?** Don't forget to:
1. Create your superadmin account
2. Configure organization settings
3. Set up backups
4. Enable SSL
5. Test all features
6. Monitor logs

**Need Help?** Check the troubleshooting sections in the deployment guides.
