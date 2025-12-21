# Configuration Guide

System configuration options for the Flight School Management System.

---

## Accessing Settings

**Navigation:** Settings → Flight School → Configuration

---

## General Settings

### Organization Information

| Setting | Description |
|---------|-------------|
| School Name | Your flight school's official name |
| Address | Physical location |
| Phone | Contact number |
| Email | Official email address |
| Logo | Organization logo (displayed in reports) |

### Regulatory Settings

| Setting | Options |
|---------|---------|
| Regulatory Authority | EASA, FAA, or Other |
| Country | Primary country of operation |
| License Prefix | Default prefix for license numbers |

---

## Module Configuration

### Fleet Module (fs_fleet)

**Settings → Flight School → Fleet Configuration**

| Setting | Description | Default |
|---------|-------------|---------|
| Default Aircraft Status | Status for new aircraft | Available |
| Maintenance Warning Days | Days before maintenance due alert | 30 |
| Flight Hour Decimals | Decimal places for flight hours | 1 |

### People Module (fs_people)

**Settings → Flight School → People Configuration**

| Setting | Description | Default |
|---------|-------------|---------|
| Medical Warning Days | Days before medical expires alert | 60 |
| License Warning Days | Days before license expires alert | 90 |
| Default Student Status | Status for new students | Active |

---

## Server Configuration (odoo.conf)

### Essential Settings

```ini
[options]
; Database
db_host = localhost
db_port = 5432
db_user = odoo
db_password = your_password
db_name = flight_school

; Server
http_port = 8069
workers = 4

; Paths
addons_path = /path/to/addons
data_dir = /path/to/data

; Logging
log_level = info
logfile = /var/log/odoo/odoo.log
```

### Production Settings

```ini
; Security (production)
admin_passwd = STRONG_PASSWORD_HERE
list_db = False
proxy_mode = True

; Performance
workers = 4
max_cron_threads = 2
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 600
limit_time_real = 1200
```

---

## Email Configuration

### Outgoing Mail (SMTP)

**Settings → Technical → Outgoing Mail Servers**

| Field | Example Value |
|-------|---------------|
| Server | smtp.gmail.com |
| Port | 587 |
| Security | TLS |
| Username | your-email@gmail.com |
| Password | app-specific-password |

### Email Templates

Customize notification emails:
- License expiration warnings
- Medical certificate reminders
- Maintenance due alerts

---

## User Permissions

### Security Groups

| Group | Access Level |
|-------|--------------|
| Flight School / User | Read-only access |
| Flight School / Instructor | Manage training records |
| Flight School / Manager | Full operational access |
| Flight School / Admin | System configuration |

### Assigning Groups

1. Go to **Settings → Users & Companies → Users**
2. Select user
3. Under **Flight School** section, check appropriate groups
4. Save

---

## Backup Configuration

### Automated Backups

Recommended: Use `odoo-backup` cron job:

```bash
# /etc/cron.daily/odoo-backup
#!/bin/bash
pg_dump -U odoo flight_school | gzip > /backups/flight_school_$(date +%Y%m%d).sql.gz
```

### Manual Backup

```bash
pg_dump -U odoo -Fc flight_school > backup.dump
```

---

**← Previous**: [Quick Start Tutorial](Quick-Start-Tutorial) | **Next**: [User Guide](User-Guide) →
