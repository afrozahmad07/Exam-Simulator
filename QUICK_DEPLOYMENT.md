# Quick Deployment Guide
## TL;DR - Fast Track to Production

This is a condensed version for experienced users. For detailed explanations, see DEPLOYMENT_GUIDE.md.

---

## Prerequisites Checklist

- [ ] Rocky Linux 8.10 VPS with Virtualmin installed
- [ ] Domain DNS pointed to VPS IP (examsimulator.afrozahmad.com)
- [ ] GitHub repository with code
- [ ] SSH access to VPS

---

## 1. Cloudflare DNS (5 minutes)

```
1. Login to Cloudflare Dashboard
2. Add A Record:
   - Type: A
   - Name: examsimulator
   - IPv4: YOUR_VPS_IP
   - Proxy: DNS only (gray cloud)
3. Wait 5-15 minutes for propagation
```

Test: `nslookup examsimulator.afrozahmad.com`

---

## 2. Virtualmin Virtual Server (5 minutes)

```
1. Access Virtualmin: https://YOUR_VPS_IP:10000
2. Create Virtual Server:
   - Domain: examsimulator.afrozahmad.com
   - Username: examsim
   - Password: [strong password]
3. Note the home directory: /home/examsim
```

---

## 3. Deploy Application (10 minutes)

SSH as domain user:

```bash
ssh examsim@YOUR_VPS_IP
```

Clone and deploy:

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/exam-simulator.git
cd exam-simulator

# Run deployment script
chmod +x deploy.sh
./deploy.sh

# Edit environment file
nano .env
# Set: SECRET_KEY, OPENAI_API_KEY, GEMINI_API_KEY
# Change FLASK_ENV=production, FLASK_DEBUG=False

# Set up systemd service (requires sudo password)
sudo ./setup-systemd.sh

# Create superadmin
source venv/bin/activate
python create_superadmin.py

# Start service
sudo systemctl start exam_simulator
sudo systemctl enable exam_simulator

# Check status
sudo systemctl status exam_simulator
```

---

## 4. Configure Web Server (10 minutes)

### For Nginx:

1. Virtualmin → Select your server → Server Configuration → Edit Directives
2. Add content from `nginx-virtualmin-config.conf`
3. Test and reload:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### For Apache:

1. Virtualmin → Select your server → Server Configuration → Edit Directives
2. Add content from `apache-virtualmin-config.conf`
3. Enable modules and reload:

```bash
sudo dnf install mod_proxy_html -y
sudo apachectl configtest
sudo systemctl reload httpd
```

---

## 5. SSL Certificate (5 minutes)

### Via Virtualmin:
```
Server Configuration → SSL Certificate → Let's Encrypt → Request Certificate
```

### Via Command Line:
```bash
sudo dnf install certbot python3-certbot-nginx -y
sudo certbot --nginx -d examsimulator.afrozahmad.com
```

---

## 6. Verify (2 minutes)

```bash
# Check service
sudo systemctl status exam_simulator

# Check logs
sudo journalctl -u exam_simulator -n 50

# Test locally
curl http://127.0.0.1:8000

# Test externally
curl https://examsimulator.afrozahmad.com
```

Visit: https://examsimulator.afrozahmad.com

---

## Local Development → Production Workflow

### On Local Machine (WSL):

```bash
# Make changes
cd /home/afroz/Exam-Simulator
source venv/bin/activate
# ... edit files ...

# Test
python app.py

# Commit and push
git add .
git commit -m "Description"
git push origin main
```

### On VPS:

```bash
ssh examsim@YOUR_VPS_IP
cd ~/exam-simulator
./update-from-github.sh
```

---

## Essential Commands

```bash
# Application
sudo systemctl {start|stop|restart|status} exam_simulator
sudo journalctl -u exam_simulator -f

# Update
./update-from-github.sh

# Web Server
sudo systemctl {restart|reload} nginx    # or httpd for Apache

# Create superadmin
cd ~/exam-simulator && source venv/bin/activate && python create_superadmin.py
```

---

## Troubleshooting Quick Fixes

**502 Bad Gateway:**
```bash
sudo systemctl restart exam_simulator
sudo journalctl -u exam_simulator -n 50
```

**Permission Issues:**
```bash
sudo chown -R examsim:examsim /home/examsim/exam-simulator
chmod 600 /home/examsim/exam-simulator/.env
```

**Service Won't Start:**
```bash
sudo journalctl -u exam_simulator -n 100 --no-pager
```

**Database Issues:**
```bash
cd ~/exam-simulator
source venv/bin/activate
python init_db.py
```

---

## Files Created

**Production Configuration:**
- `.env.production` - Environment template
- `requirements-production.txt` - Production dependencies
- `wsgi.py` - WSGI entry point
- `gunicorn_config.py` - Gunicorn configuration

**Deployment Scripts:**
- `deploy.sh` - Initial deployment
- `setup-systemd.sh` - Systemd service setup
- `update-from-github.sh` - Update from Git

**Web Server Configs:**
- `nginx-virtualmin-config.conf` - Nginx configuration
- `apache-virtualmin-config.conf` - Apache configuration

**Documentation:**
- `DEPLOYMENT_GUIDE.md` - Complete guide
- `LOCAL_DEV_WORKFLOW.md` - Development workflow
- `QUICK_DEPLOYMENT.md` - This file

---

## Next Steps

1. Configure organization settings in admin panel
2. Set up backups (see DEPLOYMENT_GUIDE.md)
3. Enable Cloudflare proxy (orange cloud)
4. Configure fail2ban for security
5. Set up monitoring

For detailed information, see **DEPLOYMENT_GUIDE.md** and **LOCAL_DEV_WORKFLOW.md**.

---

**Total Time: ~45 minutes**
