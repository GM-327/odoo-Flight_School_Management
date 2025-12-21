# Personnel Management

Managing students, instructors, and staff in the Flight School system.

---

## Overview

The People module (`fs_people`) manages:
- Students and their training progress
- Instructors and qualifications
- Pilots and license tracking
- Administrative staff
- Medical certificates

---

## Student Management

### Enrolling a Student

**Navigation:** Flight School → People → Students → Create

| Field | Required | Description |
|-------|----------|-------------|
| Name | ✅ | Full legal name |
| Date of Birth | ✅ | For age verification |
| Email | ✅ | Primary contact |
| Phone | ❌ | Contact number |
| Address | ❌ | Mailing address |
| Training Program | ✅ | PPL, CPL, ATPL, etc. |
| Assigned Instructor | ✅ | Primary instructor |
| Start Date | ✅ | Training start date |

### Training Programs

| Program | Description |
|---------|-------------|
| PPL | Private Pilot License |
| CPL | Commercial Pilot License |
| ATPL | Airline Transport Pilot License |
| IR | Instrument Rating |
| ME | Multi-Engine Rating |

### Student Statuses

| Status | Description |
|--------|-------------|
| Active | Currently enrolled and training |
| On Hold | Temporarily paused training |
| Completed | Finished program successfully |
| Withdrawn | Left the program |

---

## Instructor Management

### Adding an Instructor

**Navigation:** Flight School → People → Instructors → Create

| Field | Required | Description |
|-------|----------|-------------|
| Name | ✅ | Full name |
| Employee ID | ❌ | Internal ID |
| License Type | ✅ | CFI, CFII, MEI, etc. |
| License Number | ✅ | Certificate number |
| Expiration Date | ✅ | Certificate expiry |
| Ratings | ❌ | Aircraft type ratings |

### Instructor Ratings

| Rating | Full Name |
|--------|-----------|
| CFI | Certified Flight Instructor |
| CFII | CFI - Instrument |
| MEI | Multi-Engine Instructor |
| ATP | Airline Transport Pilot |

### Instructor Assignments

View and manage student assignments:
1. Open instructor record
2. Go to **Assignments** tab
3. See all assigned students
4. Add/remove assignments

---

## License Tracking

### License Types Tracked

| Type | Description |
|------|-------------|
| Student Pilot | Initial training certificate |
| Private Pilot | PPL certificate |
| Commercial Pilot | CPL certificate |
| Airline Transport | ATPL certificate |
| Flight Instructor | CFI certificates |

### Adding a License

1. Open person's record
2. Go to **Licenses** tab
3. Click **Add a line**
4. Enter license details:
   - Type
   - Number
   - Issue date
   - Expiration date
   - Issuing authority
   - Ratings included

### Expiration Alerts

System automatically alerts:
- 90 days before expiration
- 60 days before expiration
- 30 days before expiration
- When expired

---

## Medical Certificates

### Medical Classes

| Class | Validity | Required For |
|-------|----------|--------------|
| Class 1 | 6-12 months | Commercial/Airline pilots |
| Class 2 | 12-24 months | Private pilots |
| Class 3 | 24-60 months | Student pilots (USA) |

### Recording Medical

1. Open person's record
2. Go to **Medical** tab
3. Enter:
   - Medical class
   - Examination date
   - Expiration date
   - Issuing AME
   - Limitations (if any)

---

## Pilot Records

### Pilot Information

For qualified pilots (instructors, staff pilots):

| Section | Data Tracked |
|---------|--------------|
| Personal | Contact info, emergency contact |
| Licenses | All certificates held |
| Medical | Current medical status |
| Ratings | Type ratings, endorsements |
| Currency | Recent flight experience |

### Currency Tracking

Track pilot currency requirements:
- Day currency (3 takeoffs/landings in 90 days)
- Night currency (3 night takeoffs/landings in 90 days)
- Instrument currency (6 approaches in 6 months)
- Flight review (every 24 months)

---

## Administrative Staff

### Staff Records

**Navigation:** Flight School → People → Staff → Create

Track non-flying personnel:
- Dispatchers
- Maintenance personnel
- Administrative staff
- Management

---

## Reports

### Personnel Reports

| Report | Description |
|--------|-------------|
| Student Progress | Training status for all students |
| License Status | Upcoming expirations |
| Medical Status | Medical certificate tracking |
| Instructor Workload | Students per instructor |

---

## Best Practices

1. **Keep records current** - Update after each event
2. **Monitor expirations** - Review weekly
3. **Document everything** - Maintain audit trail
4. **Verify documents** - Check authenticity of certificates

---

**← Previous**: [Fleet Management](Fleet-Management) | **Next**: [Dashboard & Reports](Dashboard-And-Reports) →
