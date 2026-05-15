# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs scheduling wizard line module.

Purpose:
    Defines classes FsSchedulingWizardLine for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import api, fields, models, _

# Import shared constants from mixin
from ..models.fs_flight_mixin import (
    PILOT_FUNCTION_SELECTION,
    FLIGHT_CATEGORY_SELECTION,
)


class FsSchedulingWizardLine(models.TransientModel):
    """Odoo model for Scheduling Wizard Line.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.scheduling.wizard.line``.
        _description (str): Human-readable model label, ``Scheduling Wizard Line``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """
    _name = 'fs.scheduling.wizard.line'
    _description = 'Scheduling Wizard Line'
    _order = 'sequence, id'

    wizard_id = fields.Many2one('fs.scheduling.wizard', ondelete='cascade')  # type: ignore
    sequence = fields.Integer(string='Sequence', default=10)
    callsign_number = fields.Integer(string='#', help='Callsign sequence number')
    callsign_display = fields.Char(
        string='Callsign',
        compute='_compute_callsign_display',
        inverse='_inverse_callsign_display',
        store=False,
    )

    # === Category (2 options only) ===
    flight_category = fields.Selection(
        selection=FLIGHT_CATEGORY_SELECTION,
        string='Mission Category',
        default='student_training',
        required=True,
    )

    # === Pilot 1 (Primary Position) - Unified Crew Member ===
    pilot1_crew_id = fields.Many2one(
        'fs.crew.member',  # type: ignore
        string='Pilot 1',
        help="Select crew member for Pilot 1 position (student, instructor, or pilot).",
    )
    pilot1_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P1 Function',
        help="Function/role of Pilot 1",
    )

    # Computed display field for Pilot 1
    pilot1_display = fields.Char(
        string='Pilot 1',
        compute='_compute_pilot1_display',
        store=False,
    )

    # === Pilot 2 (Secondary Position) - Unified Crew Member ===
    pilot2_crew_id = fields.Many2one(
        'fs.crew.member',  # type: ignore
        string='Pilot 2',
        help="Select crew member for Pilot 2 position (instructor or pilot).",
    )
    pilot2_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P2 Function',
        help="Function/role of Pilot 2",
    )

    # Computed display field for Pilot 2
    pilot2_display = fields.Char(
        string='Pilot 2',
        compute='_compute_pilot2_display',
        store=False,
    )

    # === Flight Type (from existing model) ===
    flight_type_id = fields.Many2one(
        'fs.flight.type',
        string='Flight Type',
        compute='_compute_flight_type_id',
        store=True,
        readonly=False,
        help="Auto-determined from crew configuration, can be manually overridden.",
    )

    # === Class & Mission Info ===
    training_class_code = fields.Char(string='Class Code')
    class_type_id = fields.Many2one('fs.class.type', string='Class Type')
    aircraft_type_ids = fields.Many2many('fs.aircraft.type', string='Allowed Aircraft Types')
    aircraft_type_id = fields.Many2one(
        'fs.aircraft.type',
        string='Assigned Aircraft Type',
        help="Student's specifically assigned aircraft type from their enrollment.",
    )
    allowed_aircraft_ids = fields.Many2many(
        'fs.aircraft',
        string='Allowed Aircraft',
        compute='_compute_allowed_aircraft_ids',
        help="Computed list of allowed aircraft based on mission type (simulator vs regular).",
    )
    aircraft_id = fields.Many2one('fs.aircraft', string='Aircraft')
    mission_id = fields.Many2one('fs.flight.mission', string='Mission')
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Flight Activity',
        help="Flight activity (discipline + type) for staff training flights.",
    )
    custom_activity_id = fields.Many2one(
        comodel_name='fs.custom.flight.type',  # type: ignore
        string='Custom Activity',
        help="Non-syllabus activity (e.g. test flight, ferry).",
    )

    # Computed display field for activity
    activity_display = fields.Char(
        string='Activity',
        compute='_compute_activity_display',
        store=False,
    )

    is_sim = fields.Boolean(
        string='Is Simulator',
        compute='_compute_is_sim',
        store=False,
    )
    is_exam = fields.Boolean(
        string='Is Exam',
        compute='_compute_is_exam',
        store=True,
    )
    duration = fields.Float(string='Duration', default=1.0)
    start_time = fields.Float(string='Start Time', default=8.0)
    end_time = fields.Float(string='ETA', compute='_compute_end_time')
    has_examinator_warning = fields.Boolean(string='Examinator Warning', default=False)
    is_locked = fields.Boolean(
        string='Lock',
        default=False,
        help="If locked, this assignment will be preserved during rescheduling.",
    )
    route_id = fields.Many2one('fs.flight.route', string='Route / Area')  # type: ignore
    is_added_mission = fields.Boolean(
        string='Added Mission',
        default=False,
        help="Mark as an extra mission that doesn't follow normal callsign sequencing. Callsign will be set to 'ADD'.",
    )
    aircraft_assignment_warning = fields.Boolean(
        string='Aircraft Assignment Warning',
        default=False,
        help="If True, no aircraft could be assigned to this flight.",
    )

    # === Computed Methods ===

    @api.depends('pilot1_crew_id', 'pilot1_function', 'flight_category')
    def _compute_pilot1_display(self):
        """Compute pilot1 display values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            if line.pilot1_crew_id:
                line.pilot1_display = line.pilot1_crew_id.name or ''  # type: ignore
            else:
                line.pilot1_display = ''

    @api.depends('pilot2_crew_id', 'pilot2_function')
    def _compute_pilot2_display(self):
        """Compute pilot2 display values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            if line.pilot2_crew_id:
                line.pilot2_display = line.pilot2_crew_id.name or ''  # type: ignore
            else:
                line.pilot2_display = ''

    @api.depends('pilot1_function', 'pilot2_function', 'is_sim')
    def _compute_flight_type_id(self):
        """Auto-determine flight type from crew configuration.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        FlightType = self.env['fs.flight.type']
        dual_type = FlightType.search([('code', '=', 'DUAL')], limit=1)
        solo_type = FlightType.search([('code', '=', 'SOLO')], limit=1)
        sim_type = FlightType.search([('code', '=', 'SIM')], limit=1)

        for line in self:
            if line.is_sim and sim_type:
                line.flight_type_id = sim_type
            elif line.pilot1_function in ('solo', 'pilot') and line.pilot2_function in ('supervisor', 'safety_pilot', False):
                # Solo: flying alone or with safety pilot/supervisor (who doesn't log PIC)
                line.flight_type_id = solo_type if solo_type else False  # type: ignore
            elif line.pilot1_function == 'instructor' and not line.pilot2_function:
                # Instructor flying alone
                line.flight_type_id = solo_type if solo_type else False  # type: ignore
            else:
                # Dual: instructor + student, or any two pilots flying together
                line.flight_type_id = dual_type if dual_type else False  # type: ignore

    @api.depends('mission_id', 'mission_id.is_sim', 'activity_id', 'activity_id.is_sim')
    def _compute_is_sim(self):
        """Compute is sim values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            if line.mission_id:
                line.is_sim = line.mission_id.is_sim  # type: ignore
            elif line.activity_id:
                line.is_sim = line.activity_id.is_sim  # type: ignore
            else:
                line.is_sim = False

    @api.depends('is_sim', 'aircraft_type_ids', 'aircraft_type_id', 'class_type_id', 'class_type_id.aircraft_type_ids')
    def _compute_allowed_aircraft_ids(self):
        """Compute allowed aircraft based on mission type.

        For simulator missions: airworthy simulators from the class type's aircraft types
        For student training: filter by student's assigned aircraft type
        For staff training / fallback: filter by allowed aircraft types from class

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        Aircraft = self.env['fs.aircraft']
        for line in self:
            if line.is_sim:
                # For simulator missions, show simulators from the class type's aircraft types
                if line.class_type_id and line.class_type_id.aircraft_type_ids:  # type: ignore
                    sim_types = line.class_type_id.aircraft_type_ids.filtered(  # type: ignore
                        lambda t: t.is_simulator  # type: ignore
                    )
                    if sim_types:
                        line.allowed_aircraft_ids = Aircraft.search([
                            ('is_airworthy', '=', True),
                            ('aircraft_type_id', 'in', sim_types.ids),  # type: ignore
                        ])
                    else:
                        # Fallback: show all airworthy simulators if none assigned to class
                        line.allowed_aircraft_ids = Aircraft.search([
                            ('is_airworthy', '=', True),
                            ('aircraft_type_id.is_simulator', '=', True),
                        ])
                else:
                    # No class type, show all airworthy simulators
                    line.allowed_aircraft_ids = Aircraft.search([
                        ('is_airworthy', '=', True),
                        ('aircraft_type_id.is_simulator', '=', True),
                    ])
            elif line.aircraft_type_id:
                # Student has a specific assigned aircraft type - use it
                line.allowed_aircraft_ids = Aircraft.search([
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id', '=', line.aircraft_type_id.id),  # type: ignore
                    ('aircraft_type_id.is_simulator', '=', False),
                ])
            elif line.aircraft_type_ids:
                # Fallback to class aircraft types (for staff training or when student has no assigned type)
                line.allowed_aircraft_ids = Aircraft.search([
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id', 'in', line.aircraft_type_ids.ids),  # type: ignore
                    ('aircraft_type_id.is_simulator', '=', False),
                ])
            else:
                # No types specified, show all non-simulator aircraft
                line.allowed_aircraft_ids = Aircraft.search([
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id.is_simulator', '=', False),
                ])

    @api.depends('mission_id', 'mission_id.is_exam', 'custom_activity_id', 'custom_activity_id.is_exam')  # type: ignore
    def _compute_is_exam(self):
        """Compute is exam values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            if line.mission_id:
                line.is_exam = line.mission_id.is_exam  # type: ignore
            elif line.custom_activity_id:
                line.is_exam = line.custom_activity_id.is_exam  # type: ignore
            else:
                line.is_exam = False

    @api.depends('activity_id', 'activity_id.code', 'custom_activity_id', 'custom_activity_id.code',  # type: ignore
                 'custom_activity_id.name', 'mission_id', 'mission_id.activity_id', 'mission_id.activity_id.code')  # type: ignore
    def _compute_activity_display(self):
        """Compute display value for activity column showing activity/custom_activity code.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            if line.mission_id and line.mission_id.activity_id:  # type: ignore
                # For student training: show mission's activity code
                line.activity_display = line.mission_id.activity_id.code or ''  # type: ignore
            elif line.activity_id:
                # For staff training with activity
                line.activity_display = line.activity_id.code or ''  # type: ignore
            elif line.custom_activity_id:
                # For staff training with custom activity
                line.activity_display = line.custom_activity_id.code or line.custom_activity_id.name or ''  # type: ignore
            else:
                line.activity_display = ''

    @api.depends('start_time', 'duration')
    def _compute_end_time(self):
        """Compute end time values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            line.end_time = (line.start_time or 0.0) + (line.duration or 0.0)

    @api.depends('callsign_number', 'is_sim', 'is_added_mission')
    def _compute_callsign_display(self):
        """Compute callsign display values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            # SIM missions never use ADD behavior
            if line.is_added_mission and not line.is_sim:
                line.callsign_display = "ADD"
                continue
            prefix = 'SIM' if line.is_sim else (line.wizard_id.callsign_prefix or 'ABS')  # type: ignore
            num = line.callsign_number or 0
            line.callsign_display = f"{prefix}{num:04d}"

    def _inverse_callsign_display(self):
        """Synchronize stored values from the inverse of callsign display.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for line in self:
            display = line.callsign_display or ''
            for prefix in ['SIM', line.wizard_id.callsign_prefix or 'ABS']:  # type: ignore
                if display.startswith(prefix):
                    display = display[len(prefix):]
                    break
            if display.isdigit():
                line.callsign_number = int(display)

    # === Onchange Methods ===

    @api.onchange('flight_category')
    def _onchange_flight_category(self):
        """Handle category change: clear and reset crew fields.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.flight_category == 'student_training':
            # Clear staff activity
            self.activity_id = False
            self.custom_activity_id = False
            # Set default functions based on crew member type
            if self.pilot1_crew_id:
                if self.pilot1_crew_id.member_type == 'student':  # type: ignore
                    self.pilot1_function = 'student'
                elif self.pilot1_crew_id.member_type == 'instructor':  # type: ignore
                    self.pilot1_function = 'instructor'
                else:
                    self.pilot1_function = 'pilot'
            if self.pilot2_crew_id:
                if self.pilot2_crew_id.member_type == 'instructor':  # type: ignore
                    self.pilot2_function = 'instructor'
                else:
                    self.pilot2_function = 'pilot'
        elif self.flight_category == 'staff_training':
            # Clear mission for staff training
            self.mission_id = False
            # Filter out students from selection if they exist
            if self.pilot1_crew_id and self.pilot1_crew_id.member_type == 'student':  # type: ignore
                self.pilot1_crew_id = False
            if self.pilot2_crew_id and self.pilot2_crew_id.member_type == 'student':  # type: ignore
                self.pilot2_crew_id = False
            # Set default functions
            if self.pilot1_crew_id:
                if self.pilot1_crew_id.member_type == 'instructor':  # type: ignore
                    self.pilot1_function = 'instructor'
                else:
                    self.pilot1_function = 'pilot'
            if self.pilot2_crew_id:
                if self.pilot2_crew_id.member_type == 'instructor':  # type: ignore
                    self.pilot2_function = 'instructor'
                else:
                    self.pilot2_function = 'pilot'

    @api.onchange('pilot1_crew_id')
    def _onchange_pilot1_crew(self):
        """Smart assignment when Pilot 1 crew member is selected.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.pilot1_crew_id:
            member_type = self.pilot1_crew_id.member_type  # type: ignore
            if member_type == 'student':
                self.pilot1_function = 'student'
                # Auto-populate class info from enrollment
                if self.pilot1_crew_id.enrollment_id:  # type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(
                        self.pilot1_crew_id.enrollment_id)  # type: ignore
                    if enrollment:
                        class_rec = enrollment.training_class_id  # type: ignore
                        class_type = class_rec.class_type_id if class_rec else False  # type: ignore
                        instructor = enrollment.instructor_id  # type: ignore

                        self.training_class_code = class_rec.code if class_rec else ''  # type: ignore
                        self.class_type_id = class_type
                        self.aircraft_type_ids = class_rec.aircraft_type_ids if class_rec else False  # type: ignore
                        self.aircraft_type_id = enrollment.aircraft_type_id  # type: ignore

                        # Auto-assign instructor to Pilot 2 if available
                        if instructor and not instructor.has_expired_qualification:  # type: ignore
                            # Find the crew member for this instructor
                            crew_member = self.env['fs.crew.member'].search([
                                ('source_model', '=', 'fs.instructor'),
                                ('source_id', '=', instructor.id)  # type: ignore
                            ], limit=1)
                            if crew_member:
                                self.pilot2_crew_id = crew_member
                                self.pilot2_function = 'instructor'
            elif member_type == 'instructor':
                self.pilot1_function = 'instructor'
            else:  # pilot
                self.pilot1_function = 'pilot'
            self._check_examinator_warning()

    @api.onchange('pilot2_crew_id')
    def _onchange_pilot2_crew(self):
        """Smart assignment when Pilot 2 crew member is selected.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.pilot2_crew_id:
            member_type = self.pilot2_crew_id.member_type  # type: ignore
            if member_type == 'student':
                self.pilot2_function = 'student'
            elif member_type == 'instructor':
                self.pilot2_function = 'instructor'
            else:  # pilot
                self.pilot2_function = 'pilot'
            self._check_examinator_warning()

    @api.onchange('pilot1_function')
    def _onchange_pilot1_function(self):
        """Handle function changes - update Pilot 2 accordingly.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.pilot1_function == 'solo':
            # Solo flight: Pilot 2 becomes supervisor (on ground)
            if self.pilot2_crew_id:
                self.pilot2_function = 'supervisor'
            else:
                self.pilot2_function = False

    @api.onchange('mission_id')
    def _onchange_mission(self):
        """Update form values when mission changes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.mission_id:
            self.duration = self.mission_id.duration_hours  # type: ignore
            # Auto-fill activity_id from mission
            if self.mission_id.activity_id:  # type: ignore
                self.activity_id = self.mission_id.activity_id  # type: ignore
            # Check if mission is solo type
            if self.mission_id.flight_type_id and self.mission_id.flight_type_id.is_solo:  # type: ignore
                self.pilot1_function = 'solo'
                if self.pilot2_crew_id:
                    self.pilot2_function = 'supervisor'
            else:
                if self.pilot1_crew_id and self.pilot1_crew_id.member_type == 'student':  # type: ignore
                    self.pilot1_function = 'student'
                if self.pilot2_crew_id and self.pilot2_crew_id.member_type == 'instructor':  # type: ignore
                    self.pilot2_function = 'instructor'
            # Clear custom activity when selecting a syllabus mission
            self.custom_activity_id = False
            self._check_examinator_warning()

    @api.onchange('activity_id')
    def _onchange_activity(self):
        """Update form values when activity changes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.activity_id:
            self.custom_activity_id = False
            if self.activity_id.discipline_id and self.activity_id.discipline_id.default_flight_duration:  # type: ignore
                self.duration = self.activity_id.discipline_id.default_flight_duration  # type: ignore
            elif not self.duration:
                self.duration = 1.0

    @api.onchange('custom_activity_id')
    def _onchange_custom_activity(self):
        """Update form values when custom activity changes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.custom_activity_id:
            self.duration = self.custom_activity_id.default_duration or 1.0  # type: ignore
            self.activity_id = False
            self.mission_id = False
            # Check examinator warning for exam custom activities (Bug #6 fix)
            if self.custom_activity_id.is_exam:  # type: ignore
                self._check_examinator_warning_for_custom_activity()
            else:
                self.has_examinator_warning = False

    # === Helper Methods ===

    def _check_examinator_warning(self):
        """Check if an examinator is required but not assigned for missions.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.mission_id and self.mission_id.is_exam:  # type: ignore
            self._check_pilot2_has_examinator_qual()
        else:
            self.has_examinator_warning = False

    def _check_examinator_warning_for_custom_activity(self):
        """Check if an examinator is required but not assigned for custom activities.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.custom_activity_id and self.custom_activity_id.is_exam:  # type: ignore
            self._check_pilot2_has_examinator_qual()
        else:
            self.has_examinator_warning = False

    def _check_pilot2_has_examinator_qual(self):
        """Check if Pilot 2 has examinator qualification.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.pilot2_crew_id and self.pilot2_crew_id.member_type == 'instructor':  # type: ignore
            # Get the actual instructor record
            instructor = self.pilot2_crew_id.get_source_record()  # type: ignore
            if instructor:
                has_qual = any(
                    q.qualification_id.is_examinator  # type: ignore
                    for q in instructor.qualification_ids  # type: ignore
                    if q.qualification_id  # type: ignore
                )
                self.has_examinator_warning = not has_qual
            else:
                self.has_examinator_warning = True
        else:
            self.has_examinator_warning = True

    # === Action Methods ===

    def action_show_examinator_warning(self):
        """Show a warning popup with available examinators.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        examinators = self.env['fs.instructor'].search([
            ('has_expired_qualification', '=', False),
            ('qualification_ids.qualification_id.is_examinator', '=', True),
        ])

        return {
            'type': 'ir.actions.act_window',
            'name': _('⚠️ Examinator Required - Select an Examinator'),
            'res_model': 'fs.instructor',
            'view_mode': 'list,form',
            'domain': [('id', 'in', examinators.ids)],
            'target': 'new',
            'context': {'create': False},
        }

    def action_move_up(self):
        """Move this line up in the sequence.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        wizard = self.wizard_id
        lines = wizard.line_ids.sorted(key=lambda l: l.sequence)  # type: ignore

        for i, line in enumerate(lines):
            if line.id == self.id and i > 0:
                prev_line = lines[i - 1]
                prev_seq = prev_line.sequence
                prev_line.sequence = self.sequence  # type: ignore
                self.sequence = prev_seq  # type: ignore
                break

        return wizard._reopen_wizard()  # type: ignore

    def action_move_down(self):
        """Move this line down in the sequence.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        wizard = self.wizard_id
        lines = wizard.line_ids.sorted(key=lambda l: l.sequence)  # type: ignore

        for i, line in enumerate(lines):
            if line.id == self.id and i < len(lines) - 1:
                next_line = lines[i + 1]
                next_seq = next_line.sequence
                next_line.sequence = self.sequence  # type: ignore
                self.sequence = next_seq  # type: ignore
                break

        return wizard._reopen_wizard()  # type: ignore

    def action_move_first(self):
        """Move this line to the first position.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        wizard = self.wizard_id
        lines = wizard.line_ids.sorted(key=lambda l: l.sequence)  # type: ignore

        if lines and lines[0].id != self.id:
            min_seq = lines[0].sequence - 1
            self.sequence = min_seq  # type: ignore

        return wizard._reopen_wizard()  # type: ignore

    def action_move_last(self):
        """Move this line to the last position.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        wizard = self.wizard_id
        lines = wizard.line_ids.sorted(key=lambda l: l.sequence)  # type: ignore

        if lines and lines[-1].id != self.id:
            max_seq = lines[-1].sequence + 1
            self.sequence = max_seq  # type: ignore

        return wizard._reopen_wizard()  # type: ignore

    def toggle_lock(self):
        """Toggle the locked status of this line.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        self.ensure_one()
        self.is_locked = not self.is_locked

    def action_save_and_close(self):
        """Save the wizard line and close the popup, returning to the wizard.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return self.wizard_id._reopen_wizard()  # type: ignore
