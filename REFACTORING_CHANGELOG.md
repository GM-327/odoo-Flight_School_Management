# Flight Scheduling Modules Refactoring Changelog

**Date:** 2026-02-04  
**Modules:** `fs_flights`, `fs_scheduling`

## Summary

This refactoring addressed inconsistencies, redundancies, and anti-patterns identified in the flight scheduling codebase. The changes improve maintainability, reduce code duplication, and fix potential runtime issues.

---

## Critical Issues Fixed

### 1. ✅ Centralized Callsign Generation Logic
**Problem:** Callsign generation logic was duplicated 5+ times across different files.

**Solution:** Created `fs_scheduling/models/fs_flight_mixin.py` with centralized methods:
- `_get_callsign_config()` - Gets prefix/threshold from config
- `_get_scheduling_config()` - Gets slot increment/buffer from config
- `_get_next_callsign()` - Generates regular callsigns (e.g., ABS0001)
- `_get_next_add_callsign()` - Generates ADD callsigns (e.g., ABS7001)

**Config-Aware Design:** Constants are defined as fallback defaults with clear documentation linking them to `res.config.settings`:
```python
# Scheduling defaults (related to res.config.settings)
DEFAULT_ADD_THRESHOLD = 7000          # flight_school.first_added_mission_number
DEFAULT_SLOT_INCREMENT_MINUTES = 15   # flight_school.scheduling_time_slot_minutes  
DEFAULT_BUFFER_MINUTES = 15           # flight_school.scheduling_buffer_minutes
```

**Files Updated:**
- NEW: `fs_scheduling/models/fs_flight_mixin.py`
- `fs_flights/wizard/fs_add_flight_wizard.py` - Now inherits from mixin

---

### 2. ✅ Fixed Record Creation in Compute Method
**Problem:** `_compute_daily_ops()` in `fs_flight.py` was creating `fs.daily.operations` and `fs.simulator.operations` records inside a computed field, causing unpredictable side effects.

**Solution:** 
- Refactored `_compute_daily_ops()` to ONLY link to existing boards
- Created new `_ensure_operations_board()` method for board creation
- Board creation now happens in `create()` and `write()` overrides

**Files Updated:**
- `fs_flights/models/fs_flight.py`

---

### 3. ✅ Removed Write Inside Onchange
**Problem:** `_onchange_atd()` and `_onchange_ata()` were calling `write()` on `self._origin`, which bypasses form validation and can cause data corruption.

**Solution:** Removed the direct `write()` calls. Status changes now apply on normal form save.

**Files Updated:**
- `fs_flights/models/fs_flight.py` (lines 568-584)

---

## Moderate Issues Fixed

### 4. ✅ Shared Constants for Selection Fields
**Problem:** `PILOT_FUNCTION_SELECTION` and `FLIGHT_CATEGORY_SELECTION` were duplicated 9+ times.

**Solution:** Defined as module-level constants in `fs_flight_mixin.py`:
```python
PILOT_FUNCTION_SELECTION = [
    ('student', 'Student'),
    ('solo', 'Solo'),
    ('instructor', 'Instructor'),
    ('safety_pilot', 'Safety Pilot'),
    ('supervisor', 'Supervisor'),
    ('pilot', 'Pilot'),
]

FLIGHT_CATEGORY_SELECTION = [
    ('student_training', '📚 Student Training'),
    ('staff_training', '👥 Pilot/Staff Training'),
]
```

**Files Updated:**
- `fs_flights/models/fs_flight.py`
- `fs_scheduling/models/fs_scheduled_flight.py`
- `fs_flights/wizard/fs_add_flight_wizard.py`
- `fs_scheduling/wizard/fs_scheduling_wizard_line.py`

---

### 5. ✅ Added Mixin Inheritance
**Problem:** Common flight logic was duplicated across models.

**Solution:** Models now inherit from `fs.flight.mixin`:
- `fs.flight` → `_inherit = ['mail.thread', 'mail.activity.mixin', 'fs.flight.mixin']`
- `fs.scheduled.flight` → `_inherit = ['mail.thread', 'mail.activity.mixin', 'fs.flight.mixin']`
- `fs.add.flight.wizard` → `_inherit = ['fs.flight.mixin']`

---

### 6. ✅ Fixed Missing @api.depends Decorator
**Problem:** `_compute_display_name()` in `fs_cancellation_reason.py` was missing `@api.depends`.

**Solution:** Added proper decorator and required import.

**Files Updated:**
- `fs_scheduling/models/fs_cancellation_reason.py`

---

### 7. ✅ Replaced Deprecated name_get() Method
**Problem:** `name_get()` is deprecated in Odoo 19.

**Solution:** Replaced with `_compute_display_name()` using `@api.depends`.

**Files Updated:**
- `fs_scheduling/models/fs_crew_member.py`

---

### 8. ✅ Added Infinite Loop Guards
**Problem:** Two `while` loops in the scheduling wizard lacked maximum iteration guards.

**Solution:** Added `max_convergence_attempts = 50` guard.

**Files Updated:**
- `fs_scheduling/wizard/fs_scheduling_wizard.py` (lines 626, 855)

---

## New Files Created

| File | Description |
|------|-------------|
| `fs_scheduling/models/fs_flight_mixin.py` | Abstract mixin with shared constants and utility methods |

---

## Files Modified

| File | Changes |
|------|---------|
| `fs_scheduling/models/__init__.py` | Added mixin import |
| `fs_flights/models/fs_flight.py` | Mixin inheritance, refactored compute, fixed onchange |
| `fs_scheduling/models/fs_scheduled_flight.py` | Mixin inheritance, shared constants |
| `fs_flights/wizard/fs_add_flight_wizard.py` | Mixin inheritance, removed duplicate code |
| `fs_scheduling/wizard/fs_scheduling_wizard_line.py` | Shared constants |
| `fs_scheduling/wizard/fs_scheduling_wizard.py` | Added loop guards |
| `fs_scheduling/models/fs_cancellation_reason.py` | Added @api.depends, api import |
| `fs_scheduling/models/fs_crew_member.py` | Replaced deprecated name_get |

---

## Testing Notes

All Python files compile successfully. To verify runtime behavior:

1. Restart Odoo server with `-u fs_scheduling,fs_flights`
2. Test flight creation from Daily Operations Board
3. Test scheduling wizard flow (step 1 → step 2 → step 3)
4. Verify callsign auto-generation works correctly
5. Test ATD/ATA entry on flight records

---

## Remaining Pyright Warnings

The remaining Pyright warnings are **false positives** caused by Odoo's dynamic model attribute system. These include:
- `Cannot access attribute "category_id" for class "BaseModel"` 
- `Cannot access attribute "date" for class "BaseModel"`
- `Cannot access attribute "get_param" for class "BaseModel"`

These are expected in Odoo development and do NOT affect runtime behavior. Type ignore comments have been added where appropriate.
