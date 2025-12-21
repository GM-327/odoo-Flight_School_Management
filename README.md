# ✈️ Flight School Management System

<p align="center">
  <img src="https://img.shields.io/badge/Odoo-19.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white" alt="Odoo 19.0"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/License-LGPL--3.0-blue?style=for-the-badge" alt="License LGPL-3.0"/>
  <img src="https://img.shields.io/badge/PostgreSQL-13+-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
</p>

<p align="center">
  <b>A comprehensive Military Flight School Management System built on Odoo 19, following EU JAR-FCL (EASA) regulations.</b>
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Module Architecture](#-module-architecture)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Development](#-development)
- [Contributing](#-contributing)
- [Security](#-security)
- [License](#-license)
- [Support](#-support)

---

## 🎯 Overview

The **Flight School Management System** is a comprehensive ERP solution designed specifically for military and civilian flight training organizations. Built on the powerful Odoo 19 framework, it provides end-to-end management of:

- 🛩️ **Aircraft Fleet** - Complete fleet management with maintenance tracking
- 👨‍✈️ **Personnel Management** - Students, instructors, and staff administration
- 📚 **Training Programs** - Curriculum management following EASA regulations
- 📊 **Scheduling & Operations** - Flight scheduling and resource allocation
- 📝 **Compliance & Documentation** - Regulatory compliance and record-keeping

### Why Choose This System?

| Feature | Benefit |
|---------|---------|
| **EASA Compliant** | Built following EU JAR-FCL regulations out of the box |
| **Modular Design** | Install only the modules you need |
| **Full Integration** | Seamlessly integrates with other Odoo apps |
| **Open Source** | Transparent, customizable, and community-driven |
| **Modern Stack** | Built on Odoo 19 with the latest technologies |

---

## ✨ Features

### Core Module (`fs_core`)
- 🔐 **Role-Based Security** - Four-tier access control (User, Instructor, Manager, Admin)
- ⚙️ **Centralized Configuration** - System-wide settings management
- 📁 **Module Framework** - Foundation for all Flight School modules

### Fleet Module (`fs_fleet`)
- ✈️ **Aircraft Registry** - Complete aircraft information management
- 🔧 **Maintenance Tracking** - Schedule and track maintenance activities
- 📈 **Flight Hours Logging** - Accurate flight time tracking
- 📋 **Airworthiness Management** - Certificate and compliance tracking

### People Module (`fs_people`)
- 👨‍🎓 **Student Management** - Enrollment, progress tracking, certifications
- 👨‍✈️ **Instructor Profiles** - Qualifications, ratings, and assignments
- 📜 **License Management** - Track all pilot certifications and renewals
- 🏥 **Medical Certificate Tracking** - Class 1/2 medical compliance

### Coming Soon
- 📅 **Training Module** - Syllabus management and progress tracking
- 🗓️ **Scheduling Module** - Resource and flight scheduling
- 📊 **Reports Module** - Advanced analytics and reporting

---

## 🏗️ Module Architecture

```
Flight_School_Management/
├── fs_core/                 # Core settings and security
│   ├── security/           # Access rights and groups
│   ├── views/              # Configuration views
│   └── models/             # Core models
│
├── fs_fleet/               # Fleet management
│   ├── models/             # Aircraft models
│   ├── views/              # Fleet views
│   ├── security/           # Fleet-specific access
│   └── data/               # Default data
│
└── fs_people/              # Personnel management
    ├── models/             # People models
    ├── views/              # Personnel views
    ├── wizards/            # Action wizards
    └── security/           # Access rights
```

---

## 📦 Requirements

### System Requirements

| Component | Minimum Version | Recommended |
|-----------|----------------|-------------|
| **Operating System** | Ubuntu 22.04 / Windows 10 | Ubuntu 24.04 / Windows 11 |
| **Python** | 3.10 | 3.12+ |
| **PostgreSQL** | 13 | 15+ |
| **RAM** | 4 GB | 8 GB+ |
| **Disk Space** | 10 GB | 50 GB+ |

### Python Dependencies

All dependencies are listed in `requirements.txt`. Key packages include:

- `psycopg2` - PostgreSQL adapter
- `lxml` - XML processing
- `Pillow` - Image handling
- `reportlab` - PDF generation
- `Werkzeug` - WSGI toolkit
- `Jinja2` - Templating engine

---

## 🚀 Installation

### Option 1: Quick Start (Development)

```bash
# 1. Clone the repository
git clone https://github.com/GM-327/odoo-Flight_School_Management.git
cd flight-school-management

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure database connection
cp odoo.conf.example odoo.conf
# Edit odoo.conf with your database settings

# 5. Initialize database and install modules
./odoo-bin -c odoo.conf -d your_database -i fs_core,fs_fleet,fs_people --stop-after-init

# 6. Start the server
./odoo-bin -c odoo.conf
```

### Option 2: Production Deployment

See the [Deployment Guide](https://github.com/GM-327/odoo-Flight_School_Management/wiki/Deployment-Guide) in our wiki for detailed production setup instructions.

### Option 3: Docker (Coming Soon)

```bash
docker-compose up -d
```

---

## ⚙️ Configuration

### Basic Configuration (`odoo.conf`)

```ini
[options]
; Database settings
db_host = localhost
db_port = 5432
db_user = odoo
db_password = your_password
db_name = flight_school

; Server settings
http_port = 8069
longpolling_port = 8072
workers = 4

; Addons path
addons_path = addons,odoo/addons

; Logging
log_level = info
logfile = /var/log/odoo/odoo.log
```

### Module Configuration

After installation, navigate to:
**Settings → Flight School → Configuration**

Here you can configure:
- Default flight school information
- Regulatory authority settings
- Notification preferences
- Integration options

---

## 📖 Usage

### Getting Started

1. **Login** to Odoo with admin credentials
2. Navigate to the **Flight School** menu
3. Configure your **organization settings**
4. Add your **aircraft fleet**
5. Register **instructors** and **students**
6. Start managing your flight school!

### Quick Actions

| Action | Navigation |
|--------|------------|
| Add Aircraft | Flight School → Fleet → Create |
| Register Student | Flight School → People → Students → Create |
| Add Instructor | Flight School → People → Instructors → Create |
| View Dashboard | Flight School → Dashboard |

For detailed documentation, see our [User Guide](https://github.com/GM-327/odoo-Flight_School_Management/wiki/User-Guide).

---

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone with development tools
git clone --recurse-submodules https://github.com/GM-327/odoo-Flight_School_Management.git

# Install development dependencies
pip install -r requirements.txt
pip install ruff pytest

# Run linting
ruff check .

# Run tests
./odoo-bin -c odoo.conf -d test_db --test-enable -i fs_core --stop-after-init
```

### Project Structure

```
.
├── addons/                     # Custom addons
│   └── Flight_School_Management/  # Main module suite
├── odoo/                       # Odoo core
├── doc/                        # Documentation
├── .github/                    # GitHub templates
├── requirements.txt            # Python dependencies
├── odoo.conf                   # Configuration file
└── README.md                   # This file
```

### AI Agent Development Support

This project includes `AGENTS.md` with guidelines for AI coding assistants. When using AI tools:

1. Refer to local Odoo 19 documentation first
2. Follow existing code patterns
3. Use the validation commands provided in AGENTS.md

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### How to Contribute

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Development Guidelines

- Follow [Odoo coding standards](https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html)
- Write tests for new features
- Update documentation as needed
- Sign the [Contributor License Agreement](doc/cla/sign-cla.md)

---

## 🔒 Security

Security is a top priority. If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Review our [Security Policy](SECURITY.md)
3. Report via our [Responsible Disclosure](https://www.odoo.com/security-report) process

### Supported Versions

| Version | Supported |
|---------|-----------|
| 19.0 | ✅ Active Development |
| 18.0 | ✅ Security fixes |
| < 18.0 | ❌ Not supported |

---

## 📄 License

This project is licensed under the **LGPL-3.0 License** - see the [LICENSE](LICENSE) file for details.

```
Flight School Management System
Copyright (C) 2024 Ghazi Marzouk

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
```

---

## 💬 Support

### Community Support

- 📋 [GitHub Issues](https://github.com/GM-327/odoo-Flight_School_Management/issues) - Bug reports and feature requests
- 💬 [GitHub Discussions](https://github.com/GM-327/odoo-Flight_School_Management/discussions) - Questions and community help
- 📖 [Wiki](https://github.com/GM-327/odoo-Flight_School_Management/wiki) - Documentation and guides


## 🙏 Acknowledgments

- [Odoo S.A.](https://www.odoo.com/) - For the amazing ERP framework
- [EASA](https://www.easa.europa.eu/) - For aviation safety standards
- All [contributors](https://github.com/GM-327/odoo-Flight_School_Management/graphs/contributors) who help improve this project

---

<p align="center">
  Made with ❤️ for the aviation training community
</p>

<p align="center">
  <a href="#-flight-school-management-system">⬆️ Back to Top</a>
</p>
