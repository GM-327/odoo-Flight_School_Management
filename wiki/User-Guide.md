# User Guide

Complete user documentation for the Flight School Management System.

## 📋 Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Navigation](#navigation)
- [Fleet Management](#fleet-management)
- [Personnel Management](#personnel-management)
- [Settings & Configuration](#settings--configuration)
- [Reports](#reports)
- [Tips & Best Practices](#tips--best-practices)

---

## Introduction

The Flight School Management System is designed to streamline the operations of flight training organizations. Whether you're managing a small flying club or a large military training facility, this system provides the tools you need.

### Key Capabilities

| Module | Purpose |
|--------|---------|
| **Core** | System settings and security |
| **Fleet** | Aircraft management |
| **People** | Students, instructors, staff |
| **Training** | Curriculum and progress (coming soon) |

### User Roles

| Role | Access Level |
|------|--------------|
| **User** | View records, create basic entries |
| **Instructor** | Manage students, log flights |
| **Manager** | Full operational access |
| **Administrator** | System configuration |

---

## Getting Started

### First Login

1. Open your browser and navigate to your Flight School URL
2. Enter your username and password
3. Click **Log in**

![Login Screen](images/login-screen.png)

### Home Dashboard

After logging in, you'll see the main dashboard with:
- **Quick Stats** - Aircraft, students, upcoming flights
- **Recent Activity** - Latest actions and updates
- **Navigation Menu** - Access to all modules

### Your Profile

Update your profile information:
1. Click your name in the top-right corner
2. Select **Preferences**
3. Configure:
   - Language
   - Timezone
   - Email notifications
   - Signature

---

## Navigation

### Main Menu Structure

```
Flight School
├── 📊 Dashboard
├── ✈️ Fleet
│   ├── Aircraft
│   ├── Maintenance
│   └── Logs
├── 👥 People
│   ├── Students
│   ├── Instructors
│   └── Staff
├── 📋 Training (coming soon)
└── ⚙️ Configuration
```

### Using Filters and Search

**Search Bar**: Type to search across all records
- Use quotes for exact matches: `"Cessna 172"`
- Use field names: `registration:N123AB`

**Filters**: Click the filter icon to:
- Filter by status (active/inactive)
- Filter by date ranges
- Create custom filters
- Save filters for later use

**Grouping**: Organize data by:
- Aircraft type
- Student status
- Instructor assignment

---

## Fleet Management

### Adding an Aircraft

1. Navigate to **Flight School → Fleet → Aircraft**
2. Click **Create**
3. Fill in required information:

| Field | Description | Required |
|-------|-------------|----------|
| Registration | Aircraft registration number | ✅ |
| Make/Model | Aircraft type (e.g., Cessna 172) | ✅ |
| Serial Number | Manufacturer serial number | ✅ |
| Year | Year of manufacture | ❌ |
| Status | Available/Maintenance/Retired | ✅ |

4. Click **Save**

### Aircraft Details

Each aircraft record includes:

**General Information**
- Registration and identification
- Make, model, and variant
- Engine details
- Equipment list

**Operational Data**
- Total flight hours
- Cycles (landings)
- Next inspection due
- Airworthiness status

**Maintenance History**
- Scheduled maintenance
- Unscheduled repairs
- Parts replacement
- Inspection records

### Scheduling Maintenance

1. Open the aircraft record
2. Click **Maintenance** tab
3. Click **Schedule Maintenance**
4. Select:
   - Maintenance type
   - Due date or hours
   - Assigned mechanic
5. Add notes or work order details
6. Click **Confirm**

### Logging Flight Time

1. Open aircraft record
2. Click **Log Flight Time**
3. Enter:
   - Flight date
   - Hobbs time (start/end)
   - Tach time (start/end)
   - Number of landings
4. The system calculates flight hours automatically

---

## Personnel Management

### Student Management

#### Enrolling a New Student

1. Go to **Flight School → People → Students**
2. Click **Create**
3. Enter student information:

**Personal Information**
- Full name
- Date of birth
- Contact details
- Emergency contact

**Training Information**
- Program type (PPL, CPL, ATPL)
- Start date
- Assigned instructor
- Medical certificate info

**Documents**
- Upload ID documents
- Medical certificates
- Previous licenses

4. Click **Save & Close**

#### Tracking Student Progress

View a student's training progress:
1. Open student record
2. Check the **Progress** tab
3. View:
   - Completed lessons
   - Flight hours logged
   - Ground school completion
   - Check ride status

### Instructor Management

#### Adding an Instructor

1. Navigate to **Flight School → People → Instructors**
2. Click **Create**
3. Enter instructor details:

| Section | Information |
|---------|-------------|
| Personal | Name, contact, photo |
| Licenses | CFI, CFII, MEI certificates |
| Ratings | Aircraft ratings, instrument |
| Availability | Schedule preferences |

4. Save the record

#### Instructor Assignments

Assign instructors to students:
1. Open instructor record
2. Go to **Assignments** tab
3. Click **Add Assignment**
4. Select student and training type
5. Set start date and expectations

### License Tracking

The system tracks all pilot certifications:

**License Types**
- Student Pilot
- Private Pilot (PPL)
- Commercial Pilot (CPL)
- Airline Transport Pilot (ATPL)
- Flight Instructor (CFI/CFII)

**For Each License**
- Issue date
- Expiration date
- Issuing authority
- Ratings included
- Limitations

**Automatic Alerts**
- 90 days before expiration
- 60 days before expiration
- 30 days before expiration

---

## Settings & Configuration

### Accessing Settings

1. Navigate to **Settings** (gear icon)
2. Select **Flight School** section
3. Configure options as needed

### Configuration Options

**Organization Settings**
- Flight school name
- Address and contact info
- Logo and branding
- Regulatory authority (FAA/EASA)

**Operational Settings**
- Default currency
- Time zone
- Flight hour calculation method
- Minimum rest requirements

**Notification Settings**
- Email notifications
- License expiry warnings
- Maintenance reminders
- Booking confirmations

### Security Groups

Manage user access levels:

| Group | Capabilities |
|-------|--------------|
| Flight School / User | View records only |
| Flight School / Instructor | Manage training records |
| Flight School / Manager | Full operational access |
| Flight School / Administrator | System configuration |

---

## Reports

### Available Reports

**Fleet Reports**
- Aircraft utilization
- Maintenance history
- Flight hours summary
- Fuel consumption

**Personnel Reports**
- Student progress
- Instructor activity
- License status
- Medical certificate tracking

**Operational Reports**
- Daily flight schedule
- Weekly summary
- Monthly statistics
- Annual review

### Generating Reports

1. Navigate to **Flight School → Reports**
2. Select report type
3. Configure parameters:
   - Date range
   - Aircraft selection
   - Student/instructor filter
4. Click **Generate**
5. View on screen or export (PDF/Excel)

### Scheduled Reports

Set up automatic report delivery:
1. Configure report parameters
2. Click **Schedule**
3. Set frequency (daily/weekly/monthly)
4. Enter recipient email addresses
5. Save schedule

---

## Tips & Best Practices

### Data Entry

✅ **Do**
- Enter data consistently
- Use standard date formats
- Keep records up to date
- Add notes for context

❌ **Don't**
- Leave required fields blank
- Use abbreviations inconsistently
- Delay entering flight logs
- Share login credentials

### Efficiency Tips

1. **Use Favorites**: Star frequently used views
2. **Keyboard Shortcuts**:
   - `Alt + C` - Create new record
   - `Alt + S` - Save
   - `Alt + D` - Discard changes
   - `Alt + Q` - Quick search
3. **Batch Operations**: Use list view to update multiple records
4. **Templates**: Create templates for common entries

### Regular Maintenance

| Task | Frequency |
|------|-----------|
| Review license expirations | Weekly |
| Update flight logs | After each flight |
| Check maintenance due | Daily |
| Backup data | Daily (automatic) |
| Review user access | Monthly |

---

## Getting Help

### In-App Help

- Click the **?** icon for contextual help
- Hover over fields for tooltips
- Check the notification center for alerts

### Support Resources

- 📖 [Wiki Documentation](Home)
- ❓ [FAQ](FAQ)
- 🐛 [Report Issues](https://github.com/GM-327/odoo-Flight_School_Management/issues)
- 💬 [Community Forum](https://github.com/GM-327/odoo-Flight_School_Management/discussions)

---

**← Previous**: [Quick Start Tutorial](Quick-Start-Tutorial) | **Next**: [Fleet Management](Fleet-Management) →
