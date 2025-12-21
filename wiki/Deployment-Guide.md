# Deployment Guide

Production deployment guide for the Flight School Management System.

---

## Deployment Options

| Method | Best For |
|--------|----------|
| Native (Linux) | Full control, best performance |
| Docker | Quick setup, containerized |
| Cloud | Managed infrastructure |

---

## Linux Production Setup

### 1. System Preparation

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-dev python3-pip python3-venv \
    postgresql postgresql-client nginx certbot \
    libxml2-dev libxslt1-dev libpq-dev git
```

### 2. Create Odoo User

```bash
sudo useradd -m -d /opt/odoo -U -r -s /bin/bash odoo
```

### 3. Install Application

```bash
sudo su - odoo
git clone https://github.com/GM-327/odoo-Flight_School_Management.git /opt/odoo/flight-school
python3 -m venv /opt/odoo/venv
source /opt/odoo/venv/bin/activate
pip install -r /opt/odoo/flight-school/requirements.txt
exit
```

### 4. Configure Database

```bash
sudo -u postgres createuser -s odoo
sudo -u postgres createdb -O odoo flight_school_prod
```

### 5. Production Config

Create `/etc/odoo.conf`:

```ini
[options]
admin_passwd = STRONG_PASSWORD
db_host = localhost
db_port = 5432
db_user = odoo
db_password = DB_PASSWORD
db_name = flight_school_prod

http_port = 8069
longpolling_port = 8072
proxy_mode = True
workers = 4

addons_path = /opt/odoo/flight-school/odoo/addons,/opt/odoo/flight-school/addons
data_dir = /opt/odoo/.local/share/Odoo

logfile = /var/log/odoo/odoo.log
log_level = warning

list_db = False
```

### 6. Systemd Service

Create `/etc/systemd/system/odoo.service`:

```ini
[Unit]
Description=Odoo Flight School
After=postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
ExecStart=/opt/odoo/venv/bin/python /opt/odoo/flight-school/odoo-bin -c /etc/odoo.conf
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable odoo
sudo systemctl start odoo
```

### 7. Nginx Configuration

Create `/etc/nginx/sites-available/odoo`:

```nginx
upstream odoo {
    server 127.0.0.1:8069;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://odoo;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Certificate

```bash
sudo certbot --nginx -d your-domain.com
```

---

## Security Checklist

- [ ] Strong admin password
- [ ] `list_db = False`
- [ ] HTTPS enabled
- [ ] Firewall configured (ports 80, 443 only)
- [ ] Regular backups
- [ ] Log monitoring

---

## Backup Strategy

### Automated Daily Backup

```bash
# /etc/cron.daily/odoo-backup
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -U odoo flight_school_prod | gzip > /backup/db_$DATE.sql.gz
tar -czf /backup/filestore_$DATE.tar.gz /opt/odoo/.local/share/Odoo/filestore/
find /backup -mtime +30 -delete
```

---

## Monitoring

### Check Status

```bash
sudo systemctl status odoo
sudo tail -f /var/log/odoo/odoo.log
```

### Health Check

```bash
curl -s http://localhost:8069/web/health
```

---

## Updates

```bash
sudo systemctl stop odoo
cd /opt/odoo/flight-school
sudo -u odoo git pull
sudo -u odoo /opt/odoo/venv/bin/pip install -r requirements.txt
sudo -u odoo /opt/odoo/venv/bin/python odoo-bin -c /etc/odoo.conf -u all --stop-after-init
sudo systemctl start odoo
```

---

**← Previous**: [Code Style Guide](Code-Style-Guide) | **Next**: [Home](Home) →
