# Flight School Management System - Full Documentation

## Overview
The Flight School Management System is a comprehensive Odoo-based ERP designed to manage flight school operations, including pilot management, fleet management, training schedules, student management, document handling, and access control.

## Module Structure

### 1. fs_core
**Purpose:** Provides central configuration and shared resources.

**Models:**
- `FsDepartment`: Manages departments with unique codes, parent-child hierarchy, and managers.
- `ResConfigSettings`: Stores global settings such as default home base ICAO code and default country.

**Dependencies:** base, base_setup, auth_signup

### 2. fs_people
**Purpose:** Manages pilots, instructors, students, and staff.

**Models include:** fs_pilot, fs_instructor, fs_student, fs_rank, fs_medical_class, fs_english_level, res_users extensions.

**Views:** Instructor availability, student profiles, and related forms.

**Demo Data:** Provided in `demo` folder.

### 3. fs_fleet
**Purpose:** Manages aircraft and fleet operations.

**Models include:** aircraft, aircraft_type.
**Views:** Aircraft management, type management.

### 4. fs_flights
**Purpose:** Manages flight operations.

**Static:** JS files for operations boards.
**Views:** Flight scheduling and tracking.

### 5. fs_training
**Purpose:** Manages student training schedules and classes.

**Data:** Class type data.
**Views:** Student views, training sessions.

### 6. fs_documents
**Purpose:** Document management.

**Static:** JS for document resizing.
**Demo Data:** Included.
**Security:** Access control defined.

### 7. fs_scheduling
**Purpose:** Advanced scheduling and timeline management.

**Models:** Cancellation reasons, wizards.
**Static:** JS timeline controller and renderer.

### 8. fs_access_control
**Purpose:** Advanced access control and policies.

**Models:** Policies, assignments, audit logs, dashboards.

## Business Logic Highlights
- Departments must have unique codes, normalized and validated.
- Managers must be active users with proper Flight School roles.
- Default home base is validated as 4-letter ICAO code.
- Scheduling enforces timeline and constraints to prevent conflicts.
- All modules consume central security groups defined in `fs_core`.
- Document module supports dynamic resizing and secure access.

## Security
- Odoo record rules and access control lists (ACLs) enforce permissions per module.
- Audit logs track access control events.

## Dependencies
- Odoo standard modules: `base`, `base_setup`, `auth_signup`
- fs_core must be installed first as it provides shared configuration and groups.

## Demo and Initial Data
- Provided for students, pilots, documents, and other modules to simulate a live environment.

## Extensibility
- New modules can inherit from `fs_core` for shared settings.
- Security groups and menus can be extended per module.
- Wizards and transient models provide configurable operations.

---

This document serves as a comprehensive guide for software development companies to replicate the Flight School Management System with complete understanding of modules, models, business rules, dependencies, security, and data.