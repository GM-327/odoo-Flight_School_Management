I'm building a MILITARY FLIGHT SCHOOL MANAGEMENT SYSTEM (inspired by https://support.aviatize.com/) as an Odoo 19 Community Edition custom module. I'm a beginner developer but understand basic programming concepts.

CRITICAL CONTEXT:
- This is a MILITARY flight school following EU JAR-FCL rules (EASA regulations)
- Training is organized by "training classes" (batches of students progressing together)
- System must be FULLY CONFIGURABLE by administrators (no hard-coded values)
- Will run on LOCAL NETWORK ONLY (no internet dependency)
- This CORE module is the foundation - other modules will depend on it
- Everything must be flexible and managed through admin configuration interface

IMPORTANT: Use Odoo 19 syntax and conventions throughout. (https://www.odoo.com/documentation/19.0/)

PROJECT SCOPE - CORE MODULE (flight_school_core):

This core module provides the foundational data models and configurations that all other modules will use. It handles organizational structure, people management, and base configurations.

═══════════════════════════════════════════════════════════════════════════

MODULE 1: TRAINING CLASS TYPE MANAGEMENT (Configurable)

Model: fs.class.type

FIELDS:
- name (char, required) - e.g., "CPL - Commercial Pilot License", "IR - Instrument Rating", "PPL - Private Pilot License", "Basic Transport", "Advanced Transport", "Multi-Engine Training"
- code (char, required, unique) - e.g., "CPL", "IR", "PPL", "BT", "AT", "ME"
- description (text) - detailed description of this training program
- color (integer) - for visual identification in UI (color picker)
- sequence (integer) - for ordering/sorting
- active (boolean, default=True)

ADDITIONAL FIELDS:
- estimated_duration_months (integer) - typical program length
- min_flight_hours_required (float) - minimum flight hours for this program
- regulation_reference (char) - e.g., "JAR-FCL 1.125", "JAR-FCL 1.200"
- is_military (boolean) - Is this military training or civilian certification?
- prerequisite_type_ids (many2many to self) - Which class types must be completed before this one?
  Example: IR requires PPL completion first

BUSINESS LOGIC:
- Code must be uppercase and unique
- Name must be unique
- Cannot delete if training classes exist with this type
- Archive instead of delete (set active=False)

VIEWS:
- List view: name, code, duration, flight hours, active status
- Form view: all fields organized in groups
- Kanban view: visual cards with color coding
- Search filters: Active/Archived, Military/Civilian, By prerequisite
- Configuration menu: Settings → Training Class Types

PRE-POPULATE DATA (data/class_type_data.xml):
Create 8-10 common training types:
- PPL (Private Pilot License) - JAR-FCL PPL
- CPL (Commercial Pilot License) - JAR-FCL CPL  
- IR (Instrument Rating) - JAR-FCL IR
- ME (Multi-Engine Rating) - JAR-FCL ME
- CPL/IR (Commercial Pilot License with IR)
- Basic Military Flight Training
- Advanced Military Flight Training
- Flight Instructor Training

═══════════════════════════════════════════════════════════════════════════

MODULE 2: TRAINING CLASS MANAGEMENT

Model: fs.training.class

DESCRIPTION:
A training class is a batch/group of students who start training together and progress through a specific training program.

FIELDS:

BASIC INFO:
- name (char, required, unique) - e.g., "CPL 2024-Alpha", "IR 2025-Bravo"
- code (char, required, unique) - short identifier, e.g., "CPL24A", "IR25B"
- class_type_id (many2one to fs.class.type, required) - What training program is this?
- start_date (date, required)
- expected_end_date (date) - can be auto-calculated from class_type.estimated_duration_months
- actual_end_date (date) - when they actually finished
- status (selection, required):
  * "draft" - Planning stage
  * "active" - Currently in training
  * "on_hold" - Temporarily suspended
  * "completed" - Training finished
  * "cancelled" - Class cancelled
- color (integer) - inherited from class_type but can override

STUDENT TRACKING:
- student_ids (one2many to fs.student) - All students in this training class
- student_count (computed) - Total number of students
- active_student_count (computed) - Students currently active
- graduated_student_count (computed) - Students who completed
- dropped_student_count (computed) - Students who left/failed

PROGRESS TRACKING:
- current_phase (char) - Free text: "Week 5 of 24", "Navigation Training", etc.
- progress_percentage (float, 0-100) - Overall completion estimate
- total_flight_hours_logged (computed) - Sum of all student hours
- average_hours_per_student (computed)

NOTES & ADMIN:
- notes (text) - General class notes
- admin_notes (text) - Private admin notes (restricted access)
- regulation_notes (text) - Specific regulatory requirements for this class

BUSINESS LOGIC:
- Auto-generate name from class_type + year + sequence if not provided
  Example: class_type="CPL", year=2024, sequence=A → "CPL 2024-Alpha"
- Cannot delete training class if students are assigned (archive instead)
- Status workflow: draft → active → (on_hold) → completed/cancelled
- Warn if actual_end_date > expected_end_date + 3 months (delayed training)
- Color inherited from class_type by default

COMPUTED FIELDS LOGIC:
- student_count: count of student_ids
- active_student_count: count where student.status = 'active'
- graduated_student_count: count where student.status = 'graduated'
- total_flight_hours_logged: sum(student_ids.total_flight_hours)
- average_hours_per_student: total_flight_hours / student_count

VIEWS:
- Tree view: name, class_type, start_date, status, student_count, chief_instructor, progress
  Row colors based on status (green=active, grey=completed, red=on_hold)
- Form view with notebooks/tabs:
  * Tab 1: General Info (basic fields)
  * Tab 2: Students (embedded tree view of students with add/remove)
  * Tab 3: Instructors (many2many widget)
  * Tab 4: Progress & Statistics (computed fields, charts if possible)
  * Tab 5: Notes (notes fields)
- Kanban view: grouped by status, showing key stats per class
- Calendar view: by start_date and end_date
- Gantt view (if possible): timeline of training classes
- Graph view: classes per year, students per class
- Pivot view: analysis by class_type, year, status

SMART BUTTONS (at top of form):
- Students (shows count, links to filtered student list)
- Instructors (shows count)
- Documents (future - shows class-related documents)
- Training Records (future)

FILTERS & SEARCH:
- Group by: Status, Class Type, Year, Chief Instructor
- Filters: Active, Completed, In Progress, Delayed (past expected end date)
- Search: by name, code, instructor name, student name

ACTIONS:
- "Archive Training Class" button (sets active=False)
- "Mark as Completed" (sets status=completed, actual_end_date=today)
- "Duplicate Training Class" (for creating next session)

═══════════════════════════════════════════════════════════════════════════

MODULE 3: RANK MANAGEMENT (Military Hierarchy - Configurable)

Model: fs.rank

DESCRIPTION:
Define military ranks that can be assigned to students and instructors. Fully configurable by admin.

FIELDS:
- name (char, required, unique) - e.g., "Cadet", "2nd Lieutenant", "Captain", "Major", "Colonel"
- code (char, required, unique) - e.g., "CDT", "2LT", "CPT", "MAJ", "COL"
- category (selection, required):
  * "cadet" - Student/Trainee
  * "officer" - Commissioned Officer
  * "nco" - Non-Commissioned Officer
  * "civilian" - Civilian contractors/instructors
- sequence (integer) - for hierarchy ordering (1=lowest, 100=highest)
- insignia (binary field, optional) - Upload rank insignia image
- description (text)
- active (boolean, default=True)

BUSINESS LOGIC:
- Cannot delete if assigned to people
- Sequence determines hierarchy (higher = more senior)
- Archive instead of delete

VIEWS:
- List view: sequence, name, code, category, active
  Sorted by sequence ascending (lowest rank first)
- Form view: all fields
- Search: by category, active/archived

PRE-POPULATE DATA (data/rank_data.xml):
Example ranks (adjust for your military):
CADETS:
- Cadet (CDT)
- Officer Cadet (OCDT)

OFFICERS:
- 2nd Lieutenant (2LT)
- Lieutenant (LT)
- Captain (CPT)
- Major (MAJ)
- Lieutenant Colonel (LTCOL)
- Colonel (COL)

CIVILIAN:
- Civilian Student (CIV)

═══════════════════════════════════════════════════════════════════════════

MODULE 4: PERSON TYPE MANAGEMENT (Configurable)

Model: fs.person.type

DESCRIPTION:
Define types of people in the system (students, instructors, staff, etc.). Similar to class types but for people classification.

FIELDS:
- name (char, required, unique) - e.g., "Student Pilot", "Flight Instructor", "Ground Instructor", "Maintenance Staff", "Administrative Staff"
- code (char, required, unique) - e.g., "STUD", "FI", "GI", "MAINT", "ADMIN"
- category (selection, required):
  * "student" - Student/Trainee
  * "instructor" - Flight/Ground Instructors
  * "staff" - Support staff
  * "other" - Other categories
- color (integer) - for visual identification
- description (text)
- sequence (integer)
- active (boolean, default=True)

BUSINESS LOGIC:
- Cannot delete if people assigned
- Archive instead of delete

VIEWS:
- List view: name, code, category, active
- Form view: all fields
- Kanban view with color coding

PRE-POPULATE DATA (data/person_type_data.xml):
STUDENTS:
- Student Pilot (STUD)

INSTRUCTORS:
- Flight Instructor (FI)
- Class Rating Instructor (CRI)
- Instrument Rating Instructor (IRI)
- Multi-Engine Instructor (MEI)
- Ground Instructor (GI)
- Chief Flight Instructor (CFI)

STAFF:
- Maintenance Staff (MAINT)
- Administrative Staff (ADMIN)
- Safety Officer (SAFETY)
- Operations Staff (OPS)

═══════════════════════════════════════════════════════════════════════════

MODULE 5: STUDENT MANAGEMENT

Model: fs.student

DESCRIPTION:
Military student pilots. Each student belongs to ONE training class at a time and has a unique callsign within that class.

FIELDS:

PERSONAL INFO:
- name (char, required) - Full name
- photo (binary field, optional)
- date_of_birth (date, required)
- age (computed from date_of_birth)
- gender (selection: Male, Female, Other, Prefer not to say)
- nationality (char)
- national_id (char) - National ID/Passport number
- email (char)
- phone (char)
- mobile (char)
- emergency_contact_name (char, required)
- emergency_contact_phone (char, required)
- emergency_contact_relationship (char)

MILITARY INFO:
- service_number (char, required, unique) - Military service number
- rank_id (many2one to fs.rank, required)
- rank_name (related field from rank_id.name) - for easy display
- enlistment_date (date, required)
- commission_date (date) - If/when commissioned as officer
- unit_assignment (char) - Home unit/squadron
- security_clearance_expiry (date)

TRAINING CLASS & CALLSIGN:
- training_class_id (many2one to fs.training.class, required) - Current training class
- class_type_id (related from training_class_id.class_type_id) - for filtering
- class_name (related from training_class_id.name) - for display
- callsign (char, required) - Pilot callsign/nickname within training class
  CONSTRAINT: Unique per training class
- person_type_id (many2one to fs.person.type, domain: category='student')
- enrollment_date (date, required) - When joined this training class
- status (selection, required):
  * "active" - Currently training
  * "on_leave" - Temporary leave
  * "medical_hold" - Medical issues
  * "academic_probation" - Academic issues
  * "graduated" - Completed training
  * "dropped" - Left program (failed/quit)
  * "transferred" - Transferred to another class/program
- status_reason (text) - Why status changed

TRAINING PROGRESS:
- total_flight_hours (float, default=0.0) - Will be computed from training module later
- total_simulator_hours (float, default=0.0)
- solo_hours (float, default=0.0)
- dual_hours (float, default=0.0) - Dual instruction hours
- last_flight_date (date) - Most recent flight
- progress_percentage (float, 0-100) (computed from fs.class.type.min_flight_hours_required)- Overall training completion

ACADEMIC:
- academic_standing (selection):
  * "excellent" - Top performer
  * "good" - Meeting standards
  * "satisfactory" - Barely meeting standards
  * "probation" - Below standards
  * "failing" - Not meeting standards
- gpa (float) - Grade Point Average (if applicable)

MEDICAL (JAR-FCL):
- medical_class (selection):
  * "class_1" - JAR-FCL Class 1 (Professional pilots)
  * "class_2" - JAR-FCL Class 2 (Private pilots)
- medical_certificate_number (char)
- medical_issue_date (date)
- medical_expiry_date (date)
- medical_status (computed):
  * "current" - Valid
  * "expiring_soon" - <30 days
  * "expired" - Past expiry
- medical_limitations (text) - Any medical restrictions

CONTACT & ADDRESS:
- street (char)
- street2 (char)
- city (char)
- state (char)
- zip (char)
- country_id (many2one to res.country)

ADMINISTRATIVE:
- notes (text) - General notes
- instructor_notes (text) - Private notes from instructors
- active (boolean, default=True) - For archiving
- create_date (datetime, automatic)
- write_date (datetime, automatic)

BUSINESS LOGIC:
- Callsign must be unique within training class (SQL constraint)
- Cannot have two active training classes (constraint)
- Age computed from date_of_birth
- Medical status computed from medical_expiry_date vs today
- Service number must be unique (constraint)
- When status changes to 'graduated' or 'dropped', training class can be cleared (optional)

COMPUTED FIELDS:
- age: (today - date_of_birth) in years
- medical_status: 
  if no expiry: 'unknown'
  if expired: 'expired'
  if <30 days: 'expiring_soon'
  else: 'current'
- class_type_id: related from training_class_id.class_type_id
- rank_name: related from rank_id.name

CONSTRAINTS (SQL):
1. UNIQUE (service_number) - no duplicate service numbers
2. UNIQUE (training_class_id, callsign) - callsign unique within training class only
3. CHECK medical_expiry_date >= medical_issue_date (if both set)

VIEWS:
- List view: 
  Columns: photo (small), service_number, name, rank, callsign, training_class, status, total_flight_hours
  Row colors: green=active, red=dropped/failing, yellow=probation/medical_hold, grey=graduated
- Form view with notebooks:
  * Tab 1: Personal & Military Info
  * Tab 2: Training Class & Progress
  * Tab 3: Medical Information
  * Tab 4: Academic Standing
  * Tab 5: Contact Information
  * Tab 6: Notes
- Kanban view: grouped by training_class, showing photo, name, callsign, rank, hours
- Calendar view: by enrollment_date or last_flight_date
- Graph view: students per class, hours distribution, status breakdown
- Pivot view: analyze by training_class, rank, status

SMART BUTTONS:
- Documents (count of documents - future module)
- Training Records (count - future module)
- Flight Hours (visual indicator)

FILTERS & SEARCH:
- Group by: Training Class, Status, Rank, Medical Status, Academic Standing
- Filters: Active, Graduated, On Leave, Medical Issues, Academic Probation, Medical Expiring Soon
- Search: by name, service_number, callsign, email

ACTIONS:
- "Change Status" wizard
- "Transfer to Training Class" wizard (change training_class_id)
- "Graduate Student" (sets status=graduated, actual end date on training class)
- "Archive Student" (sets active=False)

═══════════════════════════════════════════════════════════════════════════

MODULE 6: INSTRUCTOR MANAGEMENT (configurable)

Model: fs.instructor

DESCRIPTION:
Flight instructors, ground instructors, and other teaching staff. Can be military or civilian.

FIELDS:

PERSONAL INFO:
- name (char, required)
- photo (binary field)
- date_of_birth (date)
- gender (selection)
- nationality (char)
- email (char, required)
- phone (char)
- mobile (char, required)

MILITARY/CIVILIAN:
- instructor_type (selection, required):
  * "military_qfi" - Military Qualified Flying Instructor
  * "military_qhi" - Military Qualified Helicopter Instructor
  * "civilian_fi" - Civilian Flight Instructor
  * "ground_instructor" - Ground/Theory Instructor
  * "simulator_instructor" - Simulator/Synthetic Training
  * "contractor" - Civilian Contractor
- service_number (char) - If military
- rank_id (many2one to fs.rank) - If military
- rank_name (related from rank_id.name)
- contract_number (char) - If civilian contractor
- contract_start_date (date)
- contract_end_date (date)
- person_type_id (many2one to fs.person.type, domain: category='instructor')

QUALIFICATIONS:
- license_number (char) - Instructor license/rating number
- license_type (char) - e.g., "FI(A)", "IRI(A)", "CRI", "QFI"
- license_issue_date (date)
- ratings (text) - Free text: What they're qualified to teach
- qualification_assignments (one2many) - Each row links a qualification, manual expiry_date, computed status
- max_students (integer, default=8) - Maximum student load

CERTIFICATIONS (JAR-FCL):
- medical_class (selection): class_1/class_2/military
- medical_expiry_date (date)
- medical_status (computed)
- flight_review_date (date) - Last proficiency check
- flight_review_due (date) - Next proficiency check due

ASSIGNMENT:
- training_class_ids (many2many to fs.training.class) - Assigned training classes
- class_count (computed)
- student_count (computed) - Total students across all training classes
- is_chief_instructor (boolean) - Is this a chief/senior instructor?
- chief_of_class_ids (one2many to fs.training.class, inverse of chief_instructor_id)

AVAILABILITY & WORKLOAD:
- status (selection):
  * "available" - Active and available
  * "on_leave" - Temporary leave
  * "deployed" - Military deployment
  * "medical_hold" - Medical issues
  * "retired" - No longer active
- total_instruction_hours (float) - Career total (computed from future training module)
- hours_this_month (float) - Current month hours
- max_hours_per_month (float, default=80) - Workload limit

CONTACT:
- street (char)
- street2 (char)
- city (char)
- zip (char)
- country_id (many2one to res.country)

ADMINISTRATIVE:
- hire_date (date)
- notes (text)
- admin_notes (text) - Private admin notes
- active (boolean, default=True)

BUSINESS LOGIC:
- Email must be unique
- Qualification status computed from expiry_date per assignment
- Medical status computed from medical_expiry_date
- Cannot delete if assigned to training classes (archive instead)
- Warn if student_count > max_students (overloaded)

COMPUTED FIELDS:
- medical_status: same logic as student
- class_count: count(training_class_ids)
- student_count: sum(training_class_ids.active_student_count)

VIEWS:
  Row colors based on status
- Form view with notebooks:
  * Tab 1: Personal & Military/Civilian Info
  * Tab 2: Qualifications & Certifications
  * Tab 3: Training Class Assignments
  * Tab 4: Workload & Statistics
  * Tab 5: Contact Info
  * Tab 6: Notes
- Kanban view: grouped by instructor_type or status
- Calendar view: by availability/leave dates

SMART BUTTONS:
- Training Classes (count)
- Students (count)
- Documents (future)
- Training Records (future)

FILTERS & SEARCH:
- Filters: Available, On Leave, Chief Instructors, License Expiring Soon, Overloaded (>max students)
- Search: by name, service_number, email, ratings

═══════════════════════════════════════════════════════════════════════════

MODULE 7: AIRCRAFT MANAGEMENT (Basic - for Core)

Model: fs.aircraft

DESCRIPTION:
Training aircraft fleet. Basic model for core - will be expanded in future modules.

FIELDS:
- registration (char, required, unique) - Aircraft registration number
- aircraft_type (char, required) - e.g., "Cessna 172", "Diamond DA40", "Tecnam P2006T"
- manufacturer (char)
- model (char)
- category (selection):
  * "single_engine" - Single-Engine Piston
  * "multi_engine" - Multi-Engine
  * "complex" - Complex aircraft
  * "simulator" - Flight simulator
- serial_number (char)
- year_manufactured (integer)
- hobbs_time (float) - Current Hobbs meter reading
- total_airframe_hours (float)
- photo (binary field)
- status (selection):
  * "available" - Ready for training
  * "maintenance" - Under maintenance
  * "grounded" - Not airworthy
  * "reserved" - Reserved/not for training
- home_base (char) - Where aircraft is based
- notes (text)
- active (boolean, default=True)

VIEWS:
- List view: registration, name, aircraft_type, category, hobbs_time, status
- Form view: all fields in logical groups
- Kanban view: visual cards with photo and status

BUSINESS LOGIC:
- Registration must be unique
- Cannot delete (archive only)

PRE-POPULATE: 
- Create 5-10 sample aircraft for testing (resgistration: TS-APR, TS-DMK, TS-APX, ...)

═══════════════════════════════════════════════════════════════════════════

MODULE 8: SECURITY & ACCESS CONTROL (Configurable)

Define user groups with proper permissions:

GROUPS (security/security_groups.xml):

1. Flight School User (Basic Access)
   - View training classes (read only)
   - View own profile if linked to student/instructor
   - View aircraft (read only)
   - Cannot access configuration

2. Flight School Instructor
   - All User permissions
   - View all students
   - View assigned training classes (full access)
   - Update student progress (limited fields)
   - View all aircraft
   - Cannot delete records
   - Cannot access configuration

3. Flight School Manager
   - All Instructor permissions
   - Create/edit/delete students
   - Create/edit/delete instructors
   - Create/edit/delete training classes
   - Manage class assignments
   - Cannot access configuration

4. Flight School Administrator (Full Access)
   - All Manager permissions
   - Access ALL configuration menus:
     * Training Class Types
     * Person Types
     * Ranks
   - Create/edit/delete configuration data
   - Archive/restore records
   - Access admin notes fields
   - Full system access

ACCESS RIGHTS (security/ir.model.access.csv):

Create proper access matrix for each model and group:
- fs.class.type: User(read), Instructor(read), Manager(read), Admin(all)
- fs.training.class: User(read), Instructor(read), Manager(all), Admin(all)
- fs.rank: User(read), Instructor(read), Manager(read), Admin(all)
- fs.person.type: User(read), Instructor(read), Manager(read), Admin(all)
- fs.student: User(read own), Instructor(read all), Manager(all), Admin(all)
- fs.instructor: User(read), Instructor(read all), Manager(all), Admin(all)
- fs.aircraft: User(read), Instructor(read), Manager(all), Admin(all)

RECORD RULES (if needed):
- Instructors can only edit their assigned students/training classes
- Students can only view their own record
- Admin notes fields only visible to Admin group

═══════════════════════════════════════════════════════════════════════════

MODULE 9: MENU STRUCTURE & NAVIGATION

Main Menu: "Flight School"

Top-level menus:
├── Dashboard (future - landing page with stats)
├── Training Classes
│   ├── All Training Classes (List/kanban/calendar/gantt)
│   ├── Active Classes (filtered)
│   └── Class Planning (create new)
├── Students
│   ├── All Students
│   ├── Active Students (filtered)
│   ├── Academic Probation (filtered)
│   └── Medical Status (dashboard view)
├── Instructors
│   ├── All Instructors
│   ├── Available Instructors (filtered)
│   └── Workload Overview (pivot/graph)
├── Aircraft
│   └── Fleet Overview
├── Reports (future)
└── Configuration (Admin only)
    ├── Training Class Types
    ├── Person Types
    ├── Ranks
    ├── Security & Access Control
    └── Settings


═══════════════════════════════════════════════════════════════════════════

TECHNICAL REQUIREMENTS:

- Odoo 19 Community Edition
- Module name: flight_school_core
- Module category: Aviation/Flight School
- Depends on: base, mail (for chatter)
- License: LGPL-3
- Follow Odoo 19 conventions strictly (https://www.odoo.com/documentation/19.0/)
- Use proper ORM methods
- No external dependencies (offline operation required)
- No localStorage or sessionStorage
- Add helpful docstrings and comments
- Use proper Python naming (snake_case)
- Use proper XML naming (kebab-case for IDs)

═══════════════════════════════════════════════════════════════════════════

MODULE STRUCTURE:

flight_school_core/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── class_type.py
│   ├── training_class.py
│   ├── rank.py
│   ├── person_type.py
│   ├── student.py
│   ├── instructor.py
│   └── aircraft.py
├── views/
│   ├── class_type_views.xml
│   ├── training_class_views.xml
│   ├── rank_views.xml
│   ├── person_type_views.xml
│   ├── student_views.xml
│   ├── instructor_views.xml
│   ├── aircraft_views.xml
│   └── menu_views.xml
├── security/
│   ├── security_groups.xml
│   └── ir.model.access.csv
├── data/
│   ├── class_type_data.xml
│   ├── person_type_data.xml
│   └── rank_data.xml
├── static/
│   └── description/
│       ├── icon.png
│       └── index.html
└── README.md

═══════════════════════════════════════════════════════════════════════════

DEVELOPMENT APPROACH:

Build step-by-step in this order:

PHASE 1: Configuration Models (Foundation)
1. Module structure (__init__.py, __manifest__.py)
2. Training Class Type model + views
3. Person Type model + views
4. Rank model + views
5. Test: Can admin create/edit these configurations?

PHASE 2: Main Models
6. Student model + views (most complex)
7. Instructor model + views
8. Training Class model + views (uses class_type, students, instructors)
9. Aircraft model + views (basic)
10. Test: Can create students in training classes with callsigns?

PHASE 3: Security & Data
11. Security groups + access rights
12. Pre-populate data (class_types, person_types, ranks)
13. Test: Different user access levels work?

PHASE 4: Polish
14. Menu structure
15. Smart buttons and actions
16. Filters and search views
17. Final testing with realistic data

Please start with PHASE 1, step 1: Create the module structure and __manifest__.py.
Explain each file as you create it.
Ask me before moving to the next phase.
