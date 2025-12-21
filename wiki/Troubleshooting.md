# Troubleshooting Guide

Common issues and solutions for the Flight School Management System.

---

## Installation Issues

### PostgreSQL Connection Failed

**Error:** `psycopg2.OperationalError: could not connect to server`

**Solutions:**
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check credentials in `odoo.conf`
3. Ensure database user exists: `sudo -u postgres psql -c "\du"`
4. Check pg_hba.conf allows local connections

### Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fs_core'`

**Solutions:**
1. Verify `addons_path` in `odoo.conf` includes the Flight School directory
2. Check module folder structure
3. Update apps list: **Apps → Update Apps List**

### Port Already in Use

**Error:** `OSError: [Errno 98] Address already in use`

**Solutions:**
1. Find the process: `lsof -i :8069`
2. Change port in `odoo.conf`: `http_port = 8070`
3. Stop conflicting service

---

## Runtime Issues

### Slow Performance

**Symptoms:** Pages load slowly, timeouts

**Solutions:**
1. Increase workers: `workers = 4` (production)
2. Add RAM to server
3. Use PostgreSQL optimization
4. Enable Redis for sessions
5. Check for large attachments

### Login Issues

**Can't login / Invalid credentials**

**Solutions:**
1. Reset password via database:
   ```sql
   UPDATE res_users SET password = 'admin' WHERE login = 'admin';
   ```
2. Check user is active
3. Clear browser cookies

### Missing Menu Items

**Menus not appearing after installation**

**Solutions:**
1. Upgrade module: `./odoo-bin -u fs_core --stop-after-init`
2. Clear browser cache
3. Check user has correct access groups
4. Enable Developer Mode to debug

---

## Database Issues

### Database Backup Failed

**Solutions:**
```bash
# Manual backup
pg_dump -U odoo -Fc flight_school > backup.dump

# Restore
pg_restore -U odoo -d flight_school_new backup.dump
```

### Corrupted Database

**Solutions:**
1. Restore from backup
2. Run PostgreSQL VACUUM
3. Check disk space

---

## Getting More Help

1. Check log files: `tail -f /var/log/odoo/odoo.log`
2. Enable debug mode: `?debug=1` in URL
3. Search [GitHub Issues](https://github.com/GM-327/odoo-Flight_School_Management/issues)
4. Open a [Discussion](https://github.com/GM-327/odoo-Flight_School_Management/discussions)

---

**← Previous**: [FAQ](FAQ) | **Next**: [Changelog](Changelog) →
