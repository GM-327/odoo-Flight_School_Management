# Installation Guide

This guide covers how to install the Flight School Management System on various platforms.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
  - [Quick Installation (Development)](#quick-installation-development)
  - [Production Installation (Linux)](#production-installation-linux)
  - [Windows Installation](#windows-installation)
  - [Docker Installation](#docker-installation)
- [Post-Installation](#post-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 20 GB | 100 GB+ SSD |
| **OS** | Ubuntu 22.04 / Windows 10 | Ubuntu 24.04 / Windows 11 |

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10 - 3.12 | Runtime |
| PostgreSQL | 13+ | Database |
| Git | 2.34+ | Version control |
| Node.js | 18+ | Frontend assets (optional) |
| wkhtmltopdf | 0.12.6+ | PDF generation |

---

## Installation Methods

### Quick Installation (Development)

Best for: Testing, development, and evaluation.

```bash
# Step 1: Clone the repository
git clone https://github.com/GM-327/odoo-Flight_School_Management.git
cd flight-school-management

# Step 2: Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows PowerShell

# Step 3: Install Python dependencies
pip install --upgrade pip wheel
pip install -r requirements.txt

# Step 4: Create PostgreSQL database
sudo -u postgres createuser -s odoo
createdb flight_school

# Step 5: Copy and configure odoo.conf
cp odoo.conf.example odoo.conf
# Edit odoo.conf with your settings

# Step 6: Initialize database with modules
./odoo-bin -c odoo.conf -d flight_school -i base,fs_core,fs_fleet,fs_people --stop-after-init

# Step 7: Start Odoo
./odoo-bin -c odoo.conf
```

Access the system at: **http://localhost:8069**

---

### Production Installation (Linux)

Best for: Ubuntu/Debian production servers.

#### Step 1: System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    python3-dev python3-pip python3-venv \
    postgresql postgresql-client \
    libxml2-dev libxslt1-dev libevent-dev \
    libsasl2-dev libldap2-dev \
    libpq-dev libpng-dev libjpeg-dev \
    node-less npm \
    git wget curl

# Install wkhtmltopdf
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.jammy_amd64.deb
sudo apt install -y ./wkhtmltox_0.12.6.1-2.jammy_amd64.deb
```

#### Step 2: Create Odoo User

```bash
# Create system user
sudo useradd -m -d /opt/odoo -U -r -s /bin/bash odoo

# Switch to odoo user
sudo su - odoo
```

#### Step 3: Install Odoo

```bash
# Clone repository
git clone https://github.com/GM-327/odoo-Flight_School_Management.git /opt/odoo/flight-school

# Create virtual environment
python3 -m venv /opt/odoo/venv

# Activate and install dependencies
source /opt/odoo/venv/bin/activate
pip install --upgrade pip wheel
pip install -r /opt/odoo/flight-school/requirements.txt

# Exit odoo user
exit
```

#### Step 4: Configure PostgreSQL

```bash
# Create database user
sudo -u postgres createuser -s odoo

# Create database
sudo -u postgres createdb -O odoo flight_school_prod
```

#### Step 5: Configure Odoo

Create `/etc/odoo.conf`:

```ini
[options]
; Admin password (generate a strong one!)
admin_passwd = YOUR_STRONG_ADMIN_PASSWORD

; Database
db_host = localhost
db_port = 5432
db_user = odoo
db_password = YOUR_DB_PASSWORD
db_name = flight_school_prod

; Server
http_port = 8069
longpolling_port = 8072
proxy_mode = True
workers = 4

; Paths
addons_path = /opt/odoo/flight-school/odoo/addons,/opt/odoo/flight-school/addons
data_dir = /opt/odoo/.local/share/Odoo

; Logging
logfile = /var/log/odoo/odoo.log
log_level = warning

; Security
list_db = False
```

#### Step 6: Create Systemd Service

Create `/etc/systemd/system/odoo.service`:

```ini
[Unit]
Description=Odoo Flight School Management
After=network.target postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
ExecStart=/opt/odoo/venv/bin/python /opt/odoo/flight-school/odoo-bin -c /etc/odoo.conf
Restart=on-failure
RestartSec=5

# Security hardening
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable odoo
sudo systemctl start odoo
```

#### Step 7: Configure Nginx (Recommended)

Install and configure Nginx as reverse proxy:

```nginx
# /etc/nginx/sites-available/odoo
upstream odoo {
    server 127.0.0.1:8069;
}

upstream odoo-chat {
    server 127.0.0.1:8072;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    access_log /var/log/nginx/odoo-access.log;
    error_log /var/log/nginx/odoo-error.log;

    proxy_read_timeout 720s;
    proxy_connect_timeout 720s;
    proxy_send_timeout 720s;

    # Add headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options nosniff;

    # Proxy settings
    location / {
        proxy_pass http://odoo;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_redirect off;
    }

    location /longpolling {
        proxy_pass http://odoo-chat;
    }

    # Static files (optional, for performance)
    location ~* /web/static/ {
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://odoo;
    }

    # Gzip compression
    gzip on;
    gzip_types text/css text/plain application/json application/javascript;
    gzip_min_length 1000;
}
```

---

### Windows Installation

Best for: Development on Windows machines.

#### Step 1: Install Prerequisites

1. **Python 3.10+**: Download from [python.org](https://www.python.org/downloads/)
2. **PostgreSQL 15**: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
3. **Git**: Download from [git-scm.com](https://git-scm.com/download/win)
4. **Visual C++ Build Tools**: Install from Visual Studio Installer

#### Step 2: Clone and Setup

```powershell
# Clone repository
git clone https://github.com/GM-327/odoo-Flight_School_Management.git
cd flight-school-management

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install --upgrade pip wheel
pip install -r requirements.txt
```

#### Step 3: Configure Database

```powershell
# Using psql or pgAdmin, create database
# CREATE USER odoo WITH PASSWORD 'password';
# CREATE DATABASE flight_school OWNER odoo;
```

#### Step 4: Configure and Run

```powershell
# Create odoo.conf with your settings
# Key settings for Windows:
# addons_path = D:\path\to\flight-school\odoo\addons,D:\path\to\flight-school\addons

# Start Odoo
python odoo-bin -c odoo.conf
```

---

### Docker Installation

Best for: Quick deployment and containerized environments.

#### docker-compose.yml

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
      POSTGRES_DB: postgres
    volumes:
      - db-data:/var/lib/postgresql/data

  odoo:
    build: .
    depends_on:
      - db
    ports:
      - "8069:8069"
      - "8072:8072"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
    volumes:
      - odoo-data:/var/lib/odoo
      - ./addons:/mnt/extra-addons

volumes:
  db-data:
  odoo-data:
```

#### Dockerfile

```dockerfile
FROM odoo:19.0

USER root

# Copy custom addons
COPY ./addons/Flight_School_Management /mnt/extra-addons/

# Install additional Python packages if needed
# RUN pip3 install some-package

USER odoo
```

#### Running Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f odoo

# Initialize database
docker-compose exec odoo odoo -d flight_school -i fs_core,fs_fleet,fs_people --stop-after-init

# Restart
docker-compose restart odoo
```

---

## Post-Installation

### Initial Setup

1. **Access the system**: Navigate to `http://your-server:8069`
2. **Create database** (if not already created)
3. **Set admin password**: Use a strong password!
4. **Install modules**:
   - Go to Apps → Update Apps List
   - Search for "Flight School"
   - Install: fs_core, fs_fleet, fs_people

### Security Checklist

- [ ] Change default admin password
- [ ] Configure `admin_passwd` in odoo.conf
- [ ] Set `list_db = False` in production
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Enable fail2ban for Odoo

---

## Verification

Verify your installation is working:

```bash
# Check Odoo is running
curl http://localhost:8069/web/health

# Check database connection
psql -U odoo -d flight_school -c "SELECT version();"

# Check module installation
./odoo-bin shell -c odoo.conf -d flight_school
>>> self.env['ir.module.module'].search([('name', 'like', 'fs_%')])
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port 8069 already in use | Change `http_port` in odoo.conf or stop conflicting service |
| PostgreSQL connection failed | Verify PostgreSQL is running and credentials are correct |
| Module not found | Check `addons_path` in odoo.conf |
| Permission denied | Check file ownership and permissions |
| Slow performance | Increase workers, add RAM, use SSD |

### Getting Help

1. Check [Troubleshooting](Troubleshooting) wiki page
2. Search [GitHub Issues](https://github.com/GM-327/odoo-Flight_School_Management/issues)
3. Ask in [Discussions](https://github.com/GM-327/odoo-Flight_School_Management/discussions)

---

**Next**: [Quick Start Tutorial](Quick-Start-Tutorial) →
