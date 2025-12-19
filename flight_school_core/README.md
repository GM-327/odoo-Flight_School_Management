# Flight School Core Module

**Version:** 0.1  
**License:** LGPL-3  
**Category:** Aviation/Flight School

## Description

This is the core/foundation module for a **Military Flight School Management System** following EU JAR-FCL (EASA) regulations.

This module provides the foundational data models and configurations that all other flight school modules will depend on.

## Features

### Training Class Type Management
- Define training programs (PPL, CPL, IR, etc.)
- Set estimated duration and flight hours
- Configure regulatory references (JAR-FCL)
- Track prerequisites between programs
- Support for both military and civilian training

### Person Type Management
- Classify people in the system (students, instructors, staff)
- Category-based organization
- Visual color coding

### Rank Management
- Military rank hierarchy configuration
- Support for cadets, officers, NCOs, and civilians
- Hierarchy ordering for seniority

### Security & Access Control
- **User**: Basic read access
- **Instructor**: View students and progress
- **Manager**: Full CRUD on operational data
- **Administrator**: Full access including configuration

## Installation

1. Place this module in your Odoo addons directory
2. Update the Apps List (Apps → Update Apps List)
3. Search for "Flight School Core" and install

## Configuration

After installation:
1. Go to Flight School → Configuration
2. Review and customize pre-populated data:
   - Training Class Types
   - Person Types
   - Military Ranks

## Dependencies

- `base`
- `mail`

## Technical Information

- Odoo 19 Community Edition
- No external dependencies
- Suitable for offline/local network operation

## Module Structure

```
flight_school_core/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── class_type.py
│   ├── person_type.py
│   └── rank.py
├── views/
│   ├── class_type_views.xml
│   ├── person_type_views.xml
│   ├── rank_views.xml
│   └── menu_views.xml
├── security/
│   ├── security_groups.xml
│   └── ir.model.access.csv
├── data/
│   ├── class_type_data.xml
│   ├── person_type_data.xml
│   └── rank_data.xml
└── static/
    └── description/
        ├── icon.png
        └── index.html
```

## Future Modules

This core module will be extended by:
- `flight_school_training` - Training class and student management
- `flight_school_scheduling` - Flight scheduling and booking
- `flight_school_documents` - Document management
- `flight_school_reports` - Reporting and analytics

## Support

For issues or feature requests, please contact the development team.
