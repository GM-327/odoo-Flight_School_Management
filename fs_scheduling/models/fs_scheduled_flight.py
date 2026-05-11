# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

# Import shared constants from mixin
from .fs_flight_mixin import (
    FLIGHT_CATEGORY_SELECTION,
    PILOT_FUNCTION_SELECTION,
)


class FsScheduledFlight(models.Model):
    """Instances of flight missions scheduled for specific resources and times."""

    _name = 'fs.scheduled.flight'
    _description = 'Scheduled Flight'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fs.flight.mixin']
    _order = 'is_sim asc, start_datetime asc, callsign asc'

    callsign = fields.Char(
        string='Callsign',
        required=True,
        tracking=True,
        index='trigram',
        help="Flight callsign. Can be auto-generated (PREFIX+NNNN) or manual 'ADD'.",
    )
    date = fields.Date(
        string='Date',
        required=True,
        index=True,
        default=lambda self: self._default_date(),
    )
    start_time = fields.Float(
        string='Start Time',
        required=True,
        aggregator=None,
        help="Beginning of the flight (e.g., 8.5 = 08:30).",
    )
    duration = fields.Float(
        string='Duration (Hours)',
        default=1.0,
    )
    end_time = fields.Float(
        string='End Time',
        compute='_compute_end_time',
        store=True,
    )
    start_datetime = fields.Datetime(
        string='Start Datetime',
        compute='_compute_datetimes',
        store=True,
    )
    end_datetime = fields.Datetime(
        string='End Datetime',
        compute='_compute_datetimes',
        store=True,
    )

    # === Date Parts for Grouping ===
    date_year = fields.Char(string='Year', compute='_compute_date_parts', store=True)
    date_month = fields.Char(string='Month', compute='_compute_date_parts', store=True)
    date_day = fields.Char(string='Day', compute='_compute_date_parts', store=True)

    # === Category (2 options only) ===
    flight_category = fields.Selection(
        selection=FLIGHT_CATEGORY_SELECTION,
        string='Mission Category',
        default='student_training',
        required=True,
        tracking=True,
        help="Student Training: Student + Instructor/Supervisor. "
             "Staff Training: Pilots and instructors for proficiency, ferry, tests, etc.",
    )

    # === Pilot 1 (Primary Position) - Unified Crew Member ===
    pilot1_crew_id = fields.Many2one(
        comodel_name='fs.crew.member',
        string='Pilot 1',
        ondelete='restrict',
        tracking=True,
        help="Select crew member for Pilot 1 position (student, instructor, or pilot).",
    )
    pilot1_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P1 Function',
        help="Function/role of Pilot 1",
    )

    # Computed display for Pilot 1
    pilot1_display = fields.Char(
        string='Pilot 1',
        compute='_compute_pilot1_display',
        store=True,
    )

    # Related fields from crew member for backward compatibility
    student_id = fields.Many2one(
        comodel_name='fs.student',
        compute='_compute_student_fields',
        store=True,
        readonly=True,
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        compute='_compute_student_fields',
        store=True,
        readonly=True,
    )

    # === Pilot 2 (Secondary Position) - Unified Crew Member ===
    pilot2_crew_id = fields.Many2one(
        comodel_name='fs.crew.member',
        string='Pilot 2',
        ondelete='restrict',
        tracking=True,
        help="Select crew member for Pilot 2 position (instructor or pilot).",
        group_expand='_read_group_crew_ids',
    )
    pilot2_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P2 Function',
        help="Function/role of Pilot 2",
    )

    # Computed display for Pilot 2
    pilot2_display = fields.Char(
        string='Pilot 2',
        compute='_compute_pilot2_display',
        store=True,
    )

    # === Flight Type (from existing model) ===
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        string='Flight Type',
        compute='_compute_flight_type_id',
        store=True,
        readonly=False,
        tracking=True,
        help="Auto-determined from crew configuration, can be manually overridden.",
    )
    is_solo = fields.Boolean(
        related='flight_type_id.is_solo',
        string='Is Solo Flight',
        store=True,
    )

    # === Resources ===
    aircraft_id = fields.Many2one(
        comodel_name='fs.aircraft',
        string='Aircraft',
        required=True,
        ondelete='restrict',
        tracking=True,
        group_expand='_read_group_aircraft_ids',
    )
    aircraft_registration = fields.Char(
        related='aircraft_id.registration',
        string='Aircraft Registration',
        store=True,
    )
    # Dynamic domain for aircraft based on enrollment's allowed aircraft types
    aircraft_domain = fields.Binary(
        string='Aircraft Domain',
        compute='_compute_aircraft_domain',
    )

    # === Mission Details ===
    mission_id = fields.Many2one(
        comodel_name='fs.flight.mission',
        string='Syllabus Mission',
        ondelete='restrict',
        tracking=True,
    )
    # Dynamic domain for mission based on enrollment's class type
    mission_domain = fields.Binary(
        string='Mission Domain',
        compute='_compute_mission_domain',
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Flight Activity',
        ondelete='restrict',
        tracking=True,
        help="Flight activity (discipline + type) for staff training flights.",
    )
    is_sim = fields.Boolean(
        string='Is Simulator',
        compute='_compute_is_sim_flag',
        store=True,
    )
    is_extra = fields.Boolean(
        related='mission_id.is_extra',
        string='Extra Mission',
        store=True,
    )
    custom_activity_id = fields.Many2one(
        comodel_name='fs.custom.flight.type',
        string='Custom Activity',
        ondelete='restrict',
        help="Non-syllabus activity (e.g. test flight, ferry).",
    )
    discipline_id = fields.Many2one(
        comodel_name='fs.flight.discipline',
        string='Discipline',
        compute='_compute_discipline',
        store=True,
    )
    is_exam = fields.Boolean(
        string='Is Exam',
        related='mission_id.is_exam',
        store=True,
    )
    route_id = fields.Many2one(
        comodel_name='fs.flight.route',
        string='Route / Area',
        ondelete='restrict',
    )

    # === UI Helper Fields ===
    student_callsign = fields.Char(related='student_id.callsign', string='Student Callsign', readonly=True)
    
    flight_code = fields.Char(
        string='Flight Code',
        compute='_compute_flight_code',
        help="Code of the activity/mission (e.g. MAN-SOLO)."
    )

    @api.depends('mission_id.activity_id.code', 'activity_id.code', 'custom_activity_id.code')
    def _compute_flight_code(self):
        for record in self:
            if record.mission_id and record.mission_id.activity_id: #type: ignore
                record.flight_code = record.mission_id.activity_id.code #type: ignore
            elif record.activity_id:
                record.flight_code = record.activity_id.code #type: ignore
            elif record.custom_activity_id:
                record.flight_code = record.custom_activity_id.code #type: ignore
            else:
                record.flight_code = False

    # === Status ===
    # linked_flight_id removed (moved to fs_flights)
    # Status field removed as per user request - scheduling is planning only
    
    notes = fields.Text(string='Notes')

    # === Group Expand Methods ===

    @api.model
    def _read_group_crew_ids(self, crew_members, domain, order):
        """Show all available crew members (instructors/pilots) for grouping in timeline/kanban views."""
        return self.env['fs.crew.member'].search([
            ('member_type', 'in', ['instructor', 'pilot']),
            ('has_expired_qualification', '=', False)
        ])

    # === Computed Methods ===

    @api.depends('pilot1_crew_id', 'pilot1_function', 'flight_category')
    def _compute_pilot1_display(self):
        for record in self:
            if record.pilot1_crew_id:
                record.pilot1_display = record.pilot1_crew_id.name or ''  #type: ignore
            else:
                record.pilot1_display = ''

    @api.depends('pilot1_crew_id', 'pilot1_crew_id.member_type', 'pilot1_crew_id.enrollment_id')  #type: ignore
    def _compute_student_fields(self):
        """Compute student_id and training_class_id from crew member enrollment."""
        for record in self:
            if record.pilot1_crew_id and record.pilot1_crew_id.member_type == 'student' and record.pilot1_crew_id.enrollment_id:  #type: ignore
                enrollment = self.env['fs.student.enrollment'].browse(record.pilot1_crew_id.enrollment_id)  #type: ignore
                record.student_id = enrollment.student_id if enrollment else False  #type: ignore
                record.training_class_id = enrollment.training_class_id if enrollment else False  #type: ignore
            else:
                record.student_id = False
                record.training_class_id = False

    @api.depends('flight_category', 'pilot1_crew_id', 'pilot1_crew_id.enrollment_id')
    def _compute_aircraft_domain(self):
        """Compute dynamic domain for aircraft based on enrollment's allowed aircraft types."""
        import json
        for record in self:
            if record.flight_category == 'student_training' and record.pilot1_crew_id and record.pilot1_crew_id.member_type == 'student':  #type: ignore
                if record.pilot1_crew_id.enrollment_id:  #type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(record.pilot1_crew_id.enrollment_id)  #type: ignore
                    training_class = enrollment.training_class_id if enrollment else False  #type: ignore
                    if training_class and training_class.aircraft_type_ids:
                        aircraft_type_ids = training_class.aircraft_type_ids.ids
                        record.aircraft_domain = json.dumps([('aircraft_type_id', 'in', aircraft_type_ids)])
                    else:
                        record.aircraft_domain = json.dumps([])
                else:
                    record.aircraft_domain = json.dumps([])
            else:
                record.aircraft_domain = json.dumps([])

    @api.depends('flight_category', 'pilot1_crew_id', 'pilot1_crew_id.enrollment_id')
    def _compute_mission_domain(self):
        """Compute dynamic domain for mission based on enrollment's class type."""
        import json
        for record in self:
            if record.flight_category == 'student_training' and record.pilot1_crew_id and record.pilot1_crew_id.member_type == 'student':  #type: ignore
                if record.pilot1_crew_id.enrollment_id:  #type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(record.pilot1_crew_id.enrollment_id)  #type: ignore
                    training_class = enrollment.training_class_id if enrollment else False  #type: ignore
                    if training_class and training_class.class_type_id:
                        class_type_id = training_class.class_type_id.id
                        record.mission_domain = json.dumps([('class_type_id', '=', class_type_id)])
                    else:
                        record.mission_domain = json.dumps([])
                else:
                    record.mission_domain = json.dumps([])
            else:
                record.mission_domain = json.dumps([])

    @api.depends('pilot2_crew_id', 'pilot2_function')
    def _compute_pilot2_display(self):
        for record in self:
            if record.pilot2_crew_id:
                record.pilot2_display = record.pilot2_crew_id.name or ''  #type: ignore
            else:
                record.pilot2_display = ''

    @api.depends('pilot1_function', 'pilot2_function', 'is_sim')
    def _compute_flight_type_id(self):
        """Auto-determine flight type from crew configuration."""
        FlightType = self.env['fs.flight.type']
        dual_type = FlightType.search([('code', '=', 'DUAL')], limit=1)
        solo_type = FlightType.search([('code', '=', 'SOLO')], limit=1)
        sim_type = FlightType.search([('code', '=', 'SIM')], limit=1)
        
        for record in self:
            if record.is_sim and sim_type:
                record.flight_type_id = sim_type
            elif record.pilot1_function in ('solo', 'pilot') and record.pilot2_function in ('supervisor', 'safety_pilot', False):
                # Solo: flying alone or with safety pilot/supervisor (who doesn't log PIC)
                record.flight_type_id = solo_type if solo_type else False
            elif record.pilot1_function == 'instructor' and not record.pilot2_function:
                # Instructor flying alone
                record.flight_type_id = solo_type if solo_type else False
            else:
                # Dual: instructor + student, or any two pilots flying together
                record.flight_type_id = dual_type if dual_type else False

    # === Conflict Warning Fields (Non-blocking) ===
    has_instructor_conflict = fields.Boolean(
        string='Instructor Conflict',
        compute='_compute_instructor_conflict',
        store=True,
        help="True if the crew member (pilot 2) has overlapping flights.",
    )
    instructor_conflict_details = fields.Char(
        string='Instructor Conflict Details',
        compute='_compute_instructor_conflict',
        store=True,
    )
    has_aircraft_conflict = fields.Boolean(
        string='Aircraft Conflict',
        compute='_compute_aircraft_conflict',
        store=True,
        help="True if the aircraft has overlapping flights.",
    )
    aircraft_conflict_details = fields.Char(
        string='Aircraft Conflict Details',
        compute='_compute_aircraft_conflict',
        store=True,
    )
    has_any_conflict = fields.Boolean(
        string='Has Conflict',
        compute='_compute_has_any_conflict',
        store=True,
        help="True if there is any scheduling conflict (instructor or aircraft).",
    )

    # === Constraints & Validation ===

    def _get_buffer_timedelta(self):
        """Get the configured buffer time as a timedelta."""
        buffer_min = int(self.env['ir.config_parameter'].sudo().get_param( # type: ignore
            'flight_school.scheduling_buffer_minutes', '15'
        ))
        return timedelta(minutes=buffer_min)

    @api.depends('pilot2_crew_id', 'start_datetime', 'end_datetime')
    def _compute_instructor_conflict(self):
        """Compute instructor conflict (checking Schedule Only)."""
        buffer = self._get_buffer_timedelta()
        
        for record in self:
            record.has_instructor_conflict = False
            record.instructor_conflict_details = False
            
            if not record.pilot2_crew_id:
                continue
            if record.pilot2_crew_id.member_type != 'instructor':  # type: ignore
                continue
            if not record.start_datetime or not record.end_datetime:
                continue
            
            # 1. Check Schedule Conflicts
            conflict = self.search([
                ('id', '!=', record.id),
                ('pilot2_crew_id', '=', record.pilot2_crew_id.id),
                ('start_datetime', '<', record.end_datetime + buffer),
                ('end_datetime', '>', record.start_datetime - buffer),
            ], limit=1)
            
            if conflict:
                record.has_instructor_conflict = True
                record.instructor_conflict_details = _(
                    "%(instructor)s: conflict with PLAN '%(callsign)s' (%(start)s-%(end)s)",
                    instructor=record.pilot2_crew_id.name,  #type: ignore
                    callsign=conflict.callsign,  #type: ignore
                    start=conflict.start_datetime.strftime('%H:%M') if conflict.start_datetime else '',
                    end=conflict.end_datetime.strftime('%H:%M') if conflict.end_datetime else '',
                )

    @api.depends('aircraft_id', 'start_datetime', 'end_datetime')
    def _compute_aircraft_conflict(self):
        """Compute aircraft conflict (checking Schedule Only)."""
        buffer = self._get_buffer_timedelta()
        
        for record in self:
            record.has_aircraft_conflict = False
            record.aircraft_conflict_details = False
            
            if not record.aircraft_id:
                continue
            if not record.start_datetime or not record.end_datetime:
                continue
            
            # 1. Check Schedule
            conflict = self.search([
                ('id', '!=', record.id),
                ('aircraft_id', '=', record.aircraft_id.id),
                ('start_datetime', '<', record.end_datetime + buffer),
                ('end_datetime', '>', record.start_datetime - buffer),
            ], limit=1)
            
            if conflict:
                record.has_aircraft_conflict = True
                record.aircraft_conflict_details = _(
                    "%(aircraft)s: conflict with PLAN '%(callsign)s' (%(start)s-%(end)s)",
                    aircraft=record.aircraft_id.registration, # type: ignore
                    callsign=conflict.callsign, # type: ignore
                    start=conflict.start_datetime.strftime('%H:%M') if conflict.start_datetime else '',
                    end=conflict.end_datetime.strftime('%H:%M') if conflict.end_datetime else '',
                )

    @api.depends('has_instructor_conflict', 'has_aircraft_conflict')
    def _compute_has_any_conflict(self):
        """Compute if there is any conflict."""
        for record in self:
            record.has_any_conflict = record.has_instructor_conflict or record.has_aircraft_conflict

    # === Constraints & Validation ===

    @api.constrains('route_id', 'is_sim')
    def _check_route_required(self):
        """Route/Area is required for all non-simulator flights."""
        for record in self:
            if not record.is_sim and not record.route_id:
                raise ValidationError(_(
                    "⚠️ Route / Area is required!\n\n"
                    "Please select a Route or Area for flight: %s\n\n"
                    "Note: Routes are not required for simulator sessions."
                ) % record.callsign)

    @api.onchange('pilot1_crew_id')
    def _onchange_pilot1_crew(self):
        """Smart assignment when Pilot 1 crew member is selected."""
        if self.pilot1_crew_id:
            member_type = self.pilot1_crew_id.member_type  #type: ignore
            if member_type == 'student':
                self.pilot1_function = 'student'
                # Auto-populate instructor from enrollment
                if self.pilot1_crew_id.enrollment_id:  #type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(self.pilot1_crew_id.enrollment_id)  #type: ignore
                    if enrollment:
                        instructor = enrollment.instructor_id  #type: ignore
                        if instructor and not instructor.has_expired_qualification:
                            # Find the crew member for this instructor
                            crew_member = self.env['fs.crew.member'].search([
                                ('source_model', '=', 'fs.instructor'),
                                ('source_id', '=', instructor.id)
                            ], limit=1)
                            if crew_member:
                                self.pilot2_crew_id = crew_member
                                self.pilot2_function = 'instructor'
            elif member_type == 'instructor':
                self.pilot1_function = 'instructor'
            else:  # pilot
                self.pilot1_function = 'pilot'

    @api.onchange('pilot2_crew_id')
    def _onchange_pilot2_crew(self):
        """Smart assignment when Pilot 2 crew member is selected."""
        if self.pilot2_crew_id:
            member_type = self.pilot2_crew_id.member_type  #type: ignore
            if member_type == 'student':
                self.pilot2_function = 'student'
            elif member_type == 'instructor':
                self.pilot2_function = 'instructor'
            else:  # pilot
                self.pilot2_function = 'pilot'

    @api.onchange('flight_category')
    def _onchange_flight_category(self):
        """Handle category change: clear and reset crew fields."""
        if self.flight_category == 'student_training':
            self.activity_id = False
            self.custom_activity_id = False
            # Set functions based on crew member types
            if self.pilot1_crew_id:
                if self.pilot1_crew_id.member_type == 'student':  #type: ignore
                    self.pilot1_function = 'student'
                elif self.pilot1_crew_id.member_type == 'instructor':  #type: ignore
                    self.pilot1_function = 'instructor'
                else:
                    self.pilot1_function = 'pilot'
        elif self.flight_category == 'staff_training':
            self.mission_id = False
            # Clear students from selection (not allowed in staff training)
            if self.pilot1_crew_id and self.pilot1_crew_id.member_type == 'student':  #type: ignore
                self.pilot1_crew_id = False
            if self.pilot2_crew_id and self.pilot2_crew_id.member_type == 'student':  #type: ignore
                self.pilot2_crew_id = False

    @api.onchange('pilot1_function')
    def _onchange_pilot1_function(self):
        """Handle function changes - update Pilot 2 accordingly."""
        if self.pilot1_function == 'solo':
            if self.pilot2_crew_id:
                self.pilot2_function = 'supervisor'
            else:
                self.pilot2_function = False

    @api.onchange('mission_id')
    def _onchange_mission_id(self):
        if self.mission_id:
            self.duration = self.mission_id.duration_hours  # type: ignore
            self.custom_activity_id = False
            self.activity_id = False
            # Check if mission is solo type
            if self.mission_id.flight_type_id and self.mission_id.flight_type_id.is_solo:  # type: ignore
                self.pilot1_function = 'solo'
                if self.pilot2_crew_id:
                    self.pilot2_function = 'supervisor'

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        if self.activity_id:
            self.custom_activity_id = False

    @api.onchange('custom_activity_id')
    def _onchange_custom_activity(self):
        if self.custom_activity_id:
            self.duration = self.custom_activity_id.default_duration  # type: ignore
            self.mission_id = False
            self.activity_id = False

    # === Computes ===

    @api.depends('start_time', 'duration')
    def _compute_end_time(self):
        for record in self:
            record.end_time = record.start_time + record.duration

    @api.depends('date', 'start_time', 'end_time')
    def _compute_datetimes(self):
        """Compute datetimes from the float hour fields.

        Using timedeltas keeps the computation safe when rounded minutes reach the
        next hour or when the flight duration crosses midnight.
        """
        for record in self:
            if record.date:
                base_dt = datetime.combine(record.date, datetime.min.time())
                start_minutes = round(record.start_time * 60)
                end_minutes = round(record.end_time * 60)
                record.start_datetime = base_dt + timedelta(minutes=start_minutes)
                record.end_datetime = base_dt + timedelta(minutes=end_minutes)
            else:
                record.start_datetime = False
                record.end_datetime = False

    @api.depends('mission_id', 'mission_id.is_sim', 'activity_id', 'activity_id.is_sim')
    def _compute_is_sim_flag(self):
        for record in self:
            if record.mission_id:
                record.is_sim = record.mission_id.is_sim  # type: ignore
            elif record.activity_id:
                record.is_sim = record.activity_id.is_sim  # type: ignore
            else:
                record.is_sim = False

    @api.depends('mission_id', 'activity_id', 'custom_activity_id')
    def _compute_discipline(self):
        for record in self:
            if record.mission_id:
                record.discipline_id = record.mission_id.discipline_id  # type: ignore
            elif record.activity_id:
                record.discipline_id = record.activity_id.discipline_id  # type: ignore
            else:
                record.discipline_id = False

    @api.depends('date')
    def _compute_date_parts(self):
        for record in self:
            if record.date:
                record.date_year = record.date.strftime('%Y')
                record.date_month = record.date.strftime('%m - %B')
                record.date_day = record.date.strftime('%d')
            else:
                record.date_year = False
                record.date_month = False
                record.date_day = False

    # === Group Expand for Timeline ===

    @api.model
    def _read_group_instructor_ids(self, instructors, domain):
        """Expand all eligible instructors in timeline grouping."""
        return self.env['fs.instructor'].search([
            ('has_expired_qualification', '=', False),
        ])

    @api.model
    def _read_group_aircraft_ids(self, aircraft, domain):
        """Expand all airworthy aircraft in timeline grouping."""
        return self.env['fs.aircraft'].search([
            ('is_airworthy', '=', True),
        ])

    @api.model
    def get_timeline_groups(self, grouped_field, domain=None):
        """Return all resources for timeline grouping with rich display names."""
        
        # Helper: Status Colors (Standard Bootstrap)
        STATUS_COLORS = {
            'valid': 'success',      # Green
            'expiring': 'warning',   # Yellow/Orange
            'expired': 'danger',     # Red
            'no_expiry': 'secondary' # Gray
        }
        

        def format_hours(h_float):
            if not h_float: return "00:00"
            h = int(h_float)
            m = int((h_float - h) * 60)
            return f"{h:02d}:{m:02d}"

        if grouped_field == 'aircraft_id':
            # Parse domain to check is_sim filter state
            show_sim = True  # Default: show all (including simulators)
            hide_sim = False
            sim_only = False
            
            if domain:
                for cond in domain:
                    if isinstance(cond, (list, tuple)) and len(cond) == 3:
                        field, op, val = cond
                        if field == 'is_sim' and op == '=' and val is False:
                            hide_sim = True
                        elif field == 'is_sim' and op == '=' and val is True:
                            sim_only = True
            
            # Build aircraft search domain based on filter state
            aircraft_domain: list = [('is_airworthy', '=', True)]
            if hide_sim:
                # "Hide Simulators" filter is active - exclude simulators
                aircraft_domain.append(('aircraft_type_id.is_simulator', '=', False))
            elif sim_only:
                # "Simulators Only" filter is active - show only simulators
                aircraft_domain.append(('aircraft_type_id.is_simulator', '=', True))
            # else: show all aircraft (no additional filter)
            
            records = self.env['fs.aircraft'].search(aircraft_domain)
            groups = []
            for r in records:
                # Maintenance Status Bar
                maint_status = r.maintenance_status or 'ok' # type: ignore
                color_class = 'bg-success'
                if maint_status == 'overdue': color_class = 'bg-danger'
                elif maint_status == 'due_soon': color_class = 'bg-warning'
                
                # Image URL
                image_url = f"/web/image/fs.aircraft/{r.id}/image_128"
                
                # Rich HTML Content
                name = (
                    f"<div class='d-flex align-items-center p-2' style='min-width: 250px;'>"
                    f"  <div class='me-3'>"
                    f"    <img src='{image_url}' class='rounded-3 shadow-sm' style='width: 48px; height: 48px; object-fit: cover;' alt='Parent'/>"
                    f"  </div>"
                    f"  <div class='flex-grow-1 overflow-hidden'>"
                    f"    <div class='d-flex justify-content-between align-items-center mb-1'>"
                    f"      <strong class='text-truncate' style='font-size: 14px;'>{r.registration}</strong>" # type: ignore
                    f"      <span class='badge {color_class} rounded-pill' style='font-size: 10px;'>{format_hours(r.remaining_maintenance_hours)}h</span>" # type: ignore
                    f"    </div>"
                    f"    <div class='text-muted small text-truncate' style='font-size: 11px;'>{r.aircraft_type_id.name}</div>" # type: ignore
                    f"  </div>"
                    f"</div>"
                )
                groups.append({'id': r.id, 'display_name': name})
            return groups
            
        elif grouped_field == 'pilot2_crew_id':
            # Show instructors and pilots for grouping
            records = self.env['fs.crew.member'].search([
                ('member_type', 'in', ['instructor', 'pilot']),
                # Show all, even if expired, so they appear in timeline with red badges
            ])
            groups = []
            for r in records:
                try:
                    # fs.crew.member uses 'name' as callsign/display name
                    ident = r.name or "Unknown" # type: ignore
                    
                    # Determine role & icon
                    role_label = "Pilot"
                    if r.member_type == 'instructor': # type: ignore
                        role_label = "Instructor"
                    
                    # Image URL (Crew Member avatar)
                    image_url = "/web/static/img/placeholder.png"
                    if r.source_model and r.source_id: # type: ignore
                        image_url = f"/web/image/{r.source_model}/{r.source_id}/image_128" # type: ignore
                    
                    # Qualifications Badges
                    badges = r.qualification_badges or '' # type: ignore

                    # Generate Rich HTML
                    name = (
                        f"<div class='d-flex align-items-center p-2' style='min-width: 250px;'>"
                        f"  <div class='me-3'>"
                        f"    <img src='{image_url}' class='rounded-circle border shadow-sm' style='width: 42px; height: 42px; object-fit: cover;' "
                        f"         onerror=\"this.src='/web/static/img/placeholder.png'\" alt='User'/>"
                        f"  </div>"
                        f"  <div class='flex-grow-1 overflow-hidden'>"
                        f"    <div class='d-flex justify-content-between align-items-center mb-0'>"
                        f"      <strong class='text-dark text-truncate' style='font-size: 13px;'>{ident}</strong>"
                        f"      <span class='badge bg-light text-muted border' style='font-size: 10px;'>{role_label}</span>"
                        f"    </div>"
                        f"    <div class='mt-1 d-flex flex-wrap gap-1' style='font-size: 10px;'>"
                        f"      {badges}"
                        f"    </div>"
                        f"  </div>"
                        f"</div>"
                    )
                    groups.append({'id': r.id, 'display_name': name})
                except Exception as e:
                    groups.append({'id': r.id, 'display_name': f"ERROR: {str(e)}"})
            return groups
        return []

    # === Helpers ===

    def _default_date(self):
        """Default to next working day (Mon-Fri)."""
        today = fields.Date.context_today(self)
        next_day = today + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day

    def write(self, vals):
        """Handle timeline drag/drop by converting datetime fields to date + start_time."""
        if 'start_datetime' in vals and vals['start_datetime']:
            start_dt = vals['start_datetime']
            if isinstance(start_dt, str):
                start_dt = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
            vals['date'] = start_dt.date()
            vals['start_time'] = start_dt.hour + start_dt.minute / 60.0
            del vals['start_datetime']
        
        if 'end_datetime' in vals and vals['end_datetime']:
            end_dt = vals['end_datetime']
            if isinstance(end_dt, str):
                end_dt = datetime.fromisoformat(end_dt.replace('Z', '+00:00'))
            if 'start_time' in vals and 'date' in vals:
                start_dt = datetime.combine(vals['date'], datetime.min.time())
                start_dt = start_dt.replace(
                    hour=int(vals['start_time']),
                    minute=int((vals['start_time'] % 1) * 60)
                )
                duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
                if duration_hours > 0:
                    vals['duration'] = duration_hours
            del vals['end_datetime']
        
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('callsign') or vals.get('callsign') == '/':
                vals['callsign'] = self._generate_next_callsign(
                    date=vals.get('date'),
                    is_sim=self._is_sim_callsign_context(vals),
                )
        return super().create(vals_list)

    @api.model
    def _is_sim_callsign_context(self, vals):
        """Infer whether a new scheduled flight needs a simulator callsign."""
        mission_id = vals.get('mission_id')
        if mission_id:
            mission = self.env['fs.flight.mission'].browse(mission_id)
            return bool(mission.is_sim)

        activity_id = vals.get('activity_id')
        if activity_id:
            activity = self.env['fs.flight.activity'].browse(activity_id)
            return bool(activity.is_sim)

        return False

    def _generate_next_callsign(self, date=False, is_sim=False):
        """Generate the next callsign using the shared mixin rules."""
        reference_date = fields.Date.to_date(date) if date else None
        return self._get_next_callsign(is_sim=is_sim, date=reference_date)

    def check_conflicts(self):
        """Check for resource conflicts with 15-min buffer (Schedule Only)."""
        self.ensure_one()
        if not self.start_datetime or not self.end_datetime:
            return []

        buffer_min = int(self.env['ir.config_parameter'].sudo().get_param('flight_school.scheduling_buffer_minutes', '15')) #type: ignore
        buffer = timedelta(minutes=buffer_min)
        
        start_with_buffer = self.start_datetime - buffer
        end_with_buffer = self.end_datetime + buffer

        conflicts = []
        
        # Crew member conflict (instructor/pilot)
        if self.pilot2_crew_id:
            i_conflict = self.search([
                ('id', '!=', self.id),
                ('pilot2_crew_id', '=', self.pilot2_crew_id.id),
                ('start_datetime', '<', end_with_buffer),
                ('end_datetime', '>', start_with_buffer),
            ])
            if i_conflict:
                conflicts.append(_("Crew member %s has another flight overlap (with %d min buffer).") % (self.pilot2_crew_id.name, buffer_min)) #type: ignore

        # Aircraft conflict
        if self.aircraft_id:
            a_conflict = self.search([
                ('id', '!=', self.id),
                ('aircraft_id', '=', self.aircraft_id.id),
                ('start_datetime', '<', end_with_buffer),
                ('end_datetime', '>', start_with_buffer),
            ])
            if a_conflict:
                conflicts.append(_("Aircraft %s has another flight overlap (with %d min buffer).") % (self.aircraft_id.registration, buffer_min)) #type: ignore

        return conflicts
