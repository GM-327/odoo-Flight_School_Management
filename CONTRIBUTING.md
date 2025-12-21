# Contributing to Flight School Management System

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the Flight School Management System.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [License Agreement](#license-agreement)

---

## Code of Conduct

By participating in this project, you agree to maintain a welcoming and inclusive environment. We expect all contributors to:

- Be respectful and constructive in discussions
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

---

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports:
1. **Search existing issues** to avoid duplicates
2. **Test on latest version** to confirm the bug still exists
3. **Try to reproduce** on a clean installation

When reporting bugs, please include:
- Clear, descriptive title
- Exact steps to reproduce the issue
- Expected behavior vs actual behavior
- Screenshots or videos if applicable
- Odoo version and module versions
- Error logs or traceback

### 💡 Suggesting Enhancements

We welcome feature suggestions! Please:
1. Search existing issues to check if it's already proposed
2. Clearly describe the feature and its use case
3. Explain why this would benefit other users
4. Provide mockups or examples if possible

### 🔧 Code Contributions

We accept contributions for:
- Bug fixes
- New features (after discussion)
- Documentation improvements
- Test coverage
- Translation updates

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- PostgreSQL 13 or higher
- Git
- A code editor (VS Code recommended)

### Local Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/flight-school-management.git
cd flight-school-management

# 2. Add upstream remote
git remote add upstream https://github.com/original-org/flight-school-management.git

# 3. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create development database
createdb flight_school_dev

# 6. Configure odoo.conf for development
# Set db_name = flight_school_dev

# 7. Install modules
./odoo-bin -c odoo.conf -d flight_school_dev -i fs_core,fs_fleet,fs_people --stop-after-init
```

### Running Tests

```bash
# Run module tests
./odoo-bin -c odoo.conf -d test_db --test-enable -i fs_core --stop-after-init

# Run specific test class
./odoo-bin -c odoo.conf -d test_db --test-enable --test-tags /fs_core:TestClassName --stop-after-init

# Run with coverage (requires pytest-cov)
pytest --cov=addons/Flight_School_Management
```

### Linting

We use `ruff` for code quality:

```bash
# Check all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Check specific module
ruff check addons/Flight_School_Management/
```

---

## Coding Guidelines

### Python Style

Follow [Odoo's coding guidelines](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html) and PEP 8:

```python
# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class FlightRecord(models.Model):
    """Flight record model for tracking flight activities."""
    
    _name = 'fs.flight.record'
    _description = 'Flight Record'
    _order = 'date desc'
    
    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: _('New'),
    )
    date = fields.Date(
        string='Flight Date',
        required=True,
        default=fields.Date.context_today,
    )
    
    @api.constrains('flight_hours')
    def _check_flight_hours(self):
        """Ensure flight hours are positive."""
        for record in self:
            if record.flight_hours <= 0:
                raise ValidationError(_("Flight hours must be positive."))
```

### XML Guidelines

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Use clear, descriptive IDs -->
    <record id="view_flight_record_form" model="ir.ui.view">
        <field name="name">fs.flight.record.form</field>
        <field name="model">fs.flight.record</field>
        <field name="arch" type="xml">
            <form string="Flight Record">
                <!-- Group related fields -->
                <group>
                    <field name="name"/>
                    <field name="date"/>
                </group>
            </form>
        </field>
    </record>
</odoo>
```

### Commit Messages

Use clear, descriptive commit messages:

```
[MODULE] Short description (max 50 chars)

Longer description explaining what and why (not how).
Reference issues: fixes #123, relates to #456

- Bullet points for multiple changes
- Keep each line under 72 characters
```

Examples:
- `[fs_fleet] Add aircraft maintenance scheduling`
- `[fs_people] Fix student enrollment validation`
- `[fs_core] Improve security group definitions`

---

## Pull Request Process

### Before Submitting

1. ✅ Code follows project style guidelines
2. ✅ All tests pass locally
3. ✅ Linting passes (`ruff check .`)
4. ✅ Documentation updated if needed
5. ✅ Commits are squashed/organized logically
6. ✅ Branch is up-to-date with main

### Creating a Pull Request

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with appropriate commits

3. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request**
   - Use the PR template provided
   - Link related issues
   - Describe what changed and why
   - Add screenshots for UI changes

### PR Review Process

1. Automated checks run (tests, linting)
2. Maintainer review (usually within 1 week)
3. Address feedback if requested
4. Final approval and merge

### After Merge

- Delete your feature branch
- Pull latest changes to your local main branch
- Start on your next contribution!

---

## Issue Guidelines

### Bug Reports

Use the bug report template and include:

- [ ] Odoo version (e.g., 19.0)
- [ ] Module version (from `__manifest__.py`)
- [ ] Steps to reproduce
- [ ] Expected vs actual behavior
- [ ] Error logs/traceback
- [ ] Screenshots if applicable

### Feature Requests

- Clearly describe the proposed feature
- Explain the problem it solves
- Provide examples or mockups
- Indicate if you're willing to implement it

### Questions

For general questions:
- Check the [Wiki](https://github.com/your-org/flight-school-management/wiki) first
- Search existing issues and discussions
- Use [GitHub Discussions](https://github.com/your-org/flight-school-management/discussions) for Q&A

---

## License Agreement

### Contributor License Agreement (CLA)

By contributing to this project, you agree that:

1. Your contributions are your original work
2. You have the right to submit the contribution
3. Your contribution is licensed under LGPL-3.0
4. You grant the project maintainers rights to use your contribution

For significant contributions, you may be asked to sign a formal CLA. See [doc/cla/sign-cla.md](doc/cla/sign-cla.md) for details.

---

## Quick Reference

| Task | Command |
|------|---------|
| Run Odoo | `./odoo-bin -c odoo.conf` |
| Install module | `./odoo-bin -c odoo.conf -d odoo -i module_name --stop-after-init` |
| Upgrade module | `./odoo-bin -c odoo.conf -d odoo -u module_name --stop-after-init` |
| Run tests | `./odoo-bin -c odoo.conf -d test_db --test-enable -i module_name` |
| Lint code | `ruff check .` |

---

## Questions?

If you have questions about contributing:
- Open a [Discussion](https://github.com/your-org/flight-school-management/discussions)
- Review existing documentation
- Contact the maintainers

**Thank you for contributing to the Flight School Management System!** ✈️
