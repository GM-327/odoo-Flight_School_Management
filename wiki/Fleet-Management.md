# Fleet Management

Complete guide to managing your aircraft fleet.

---

## Overview

The Fleet module (`fs_fleet`) provides:
- Aircraft registry management
- Maintenance tracking
- Flight hour logging
- Airworthiness monitoring

---

## Aircraft Management

### Adding an Aircraft

**Navigation:** Flight School → Fleet → Aircraft → Create

| Field | Required | Description |
|-------|----------|-------------|
| Registration | ✅ | Aircraft registration (e.g., N123AB) |
| Make | ✅ | Manufacturer (e.g., Cessna) |
| Model | ✅ | Model name (e.g., 172S Skyhawk) |
| Serial Number | ✅ | Manufacturer's serial number |
| Year | ❌ | Year of manufacture |
| Status | ✅ | Available, Maintenance, Grounded, Retired |

### Aircraft Statuses

| Status | Color | Description |
|--------|-------|-------------|
| Available | 🟢 Green | Ready for flight operations |
| Maintenance | 🟡 Yellow | Scheduled maintenance in progress |
| Grounded | 🔴 Red | Unairworthy, cannot fly |
| Retired | ⚫ Grey | No longer in service |

### Aircraft Categories

Pre-configured categories:
- **Single Engine Piston** - Cessna 172, Piper Cherokee
- **Multi Engine Piston** - Piper Seneca, Beechcraft Baron
- **Turboprop** - King Air, Pilatus PC-12
- **Jet** - Citation, Phenom

---

## Maintenance Tracking

### Scheduling Maintenance

1. Open aircraft record
2. Go to **Maintenance** tab
3. Click **Schedule Maintenance**
4. Fill in details:
   - Type (100hr, Annual, Unscheduled)
   - Due date or hours
   - Description
   - Assigned mechanic

### Maintenance Types

| Type | Interval | Description |
|------|----------|-------------|
| 100-Hour | Every 100 flight hours | Required for rental/training aircraft |
| Annual | Every 12 months | Comprehensive inspection |
| Progressive | Per schedule | Distributed inspection program |
| Unscheduled | As needed | Repairs and defect fixes |

### Maintenance Alerts

Automatic alerts when:
- Maintenance is due within 30 days
- Maintenance is due within 10 hours
- Maintenance is overdue

---

## Flight Hour Tracking

### Logging Flight Time

1. Open aircraft record
2. Click **Log Flight** button
3. Enter:
   - Flight date
   - Hobbs start/end
   - Tach start/end (optional)
   - Landings count
   - Notes

### Automatic Calculations

The system automatically:
- Calculates flight duration
- Updates total aircraft hours
- Updates cycles (landings)
- Checks maintenance due status

### Time Tracking Methods

| Method | Description |
|--------|-------------|
| Hobbs Time | Engine running time |
| Tach Time | Adjusted engine time (at cruise RPM) |
| Block Time | Chock to chock |
| Flight Time | Takeoff to landing |

---

## Airworthiness Management

### Documents Tracked

| Document | Validity |
|----------|----------|
| Certificate of Airworthiness | Permanent (with valid inspections) |
| Registration Certificate | Per country requirements |
| Insurance | Annual renewal |
| Radio License | Per country requirements |

### Expiration Warnings

Configure warning periods in **Settings → Flight School → Fleet Configuration**

---

## Reports

### Available Reports

| Report | Description |
|--------|-------------|
| Fleet Status | Overview of all aircraft statuses |
| Utilization | Flight hours per aircraft |
| Maintenance Due | Upcoming maintenance items |
| Flight Log | Detailed flight history |

### Generating Reports

1. **Flight School → Reports → Fleet Reports**
2. Select report type
3. Set date range and filters
4. Click **Generate**
5. Export as PDF or Excel

---

## Best Practices

### Data Entry
- Enter flight logs same day
- Update maintenance immediately after completion
- Keep documents current

### Maintenance
- Schedule maintenance in advance
- Never fly overdue aircraft
- Document all discrepancies

---

**← Previous**: [User Guide](User-Guide) | **Next**: [Personnel Management](Personnel-Management) →
