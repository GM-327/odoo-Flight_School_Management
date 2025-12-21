# Security Policy

## 🔒 Overview

Security is a top priority for the Flight School Management System. We take all security reports seriously and investigate every report we receive.

---

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| 19.0.x  | ✅ Yes | Active development |
| 18.0.x  | ✅ Yes | Security fixes only |
| < 18.0  | ❌ No | End of life |

---

## Reporting a Vulnerability

### DO Report

- Authentication/authorization bypasses
- SQL injection vulnerabilities
- Cross-site scripting (XSS)
- Remote code execution
- Data exposure vulnerabilities
- Security misconfigurations

### DO NOT Report

- Issues in non-supported versions
- Social engineering attacks
- Physical security issues
- Vulnerabilities requiring unlikely user interaction
- Issues already publicly known

---

## Reporting Process

### Step 1: Private Disclosure

**DO NOT** open a public GitHub issue for security vulnerabilities.

- Use [our Security page](https://www.odoo.com/security-report)

### Step 2: Include Details

Please provide:
- Detailed vulnerability description
- Steps to reproduce
- Affected versions
- Potential impact
- Proof of concept (if available)

### Step 3: Response Timeline

| Phase | Timeframe |
|-------|-----------|
| Initial response | 48 hours |
| Issue confirmation | 7 days |
| Fix development | Varies by severity |
| Public disclosure | After fix released |

---

## Security Best Practices

### For Administrators

1. **Strong Passwords**: Use complex admin passwords
2. **HTTPS Only**: Always use SSL/TLS in production
3. **List DB**: Set `list_db = False` in production
4. **Firewall**: Restrict database access
5. **Updates**: Keep Odoo and modules updated
6. **Backups**: Regular encrypted backups
7. **2FA**: Enable two-factor authentication

### Configuration Checklist

```ini
# odoo.conf security settings
admin_passwd = YOUR_STRONG_PASSWORD
list_db = False
proxy_mode = True
```

---

## Acknowledgments

We thank security researchers who help keep our project safe. Responsible disclosure is appreciated.

---

## Additional Resources

- [Odoo Security](https://www.odoo.com/security-report)
- [OWASP Guidelines](https://owasp.org/)
