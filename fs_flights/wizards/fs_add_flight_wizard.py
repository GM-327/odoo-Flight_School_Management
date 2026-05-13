# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models

# Import shared constants through the Odoo addon namespace so module loading
# works reliably during registry initialization.
from odoo.addons.fs_scheduling.models.fs_flight_mixin import (
    PILOT_FUNCTION_SELECTION,
    FLIGHT_CATEGORY_SELECTION,
)


class FsAddFlightWizard(models.TransientModel):
    """Wizard for adding new flights from operations board."""

    _name = 'fs.add.flight.wizard'
    _description = 'Add Flight Wizard'
    _inherit = ['fs.flight.mixin']

    callsign = fields.Char(
        string='Callsign',
        required=True,
        default=lambda self: self._get_next_add_callsign(),
    )

    # Note: _get_next_add_callsign is now inherited from fs.flight.mixin

    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
    )
    start_time = fields.Float(
        string='Scheduled Time',
        required=True,
        default=8.0,
    )
    duration = fields.Float(
        string='Duration',
        default=1.0,
        required=True,
    )
    eta = fields.Float(
        string='ETA',
        compute='_compute_eta',
    )

    @api.depends('start_time', 'duration')
    def _compute_eta(self):
        for record in self:
            record.eta = record.start_time + record.duration

    flight_category = fields.Selection(
        selection=FLIGHT_CATEGORY_SELECTION,
        string='Category',
        default='student_training',
        required=True,
    )
    aircraft_id = fields.Many2one(
        comodel_name='fs.aircraft',
        string='Aircraft',
        required=True,
        domain="[('is_airworthy', '=', True)]",
    )
    pilot1_crew_id = fields.Many2one(
        comodel_name='fs.crew.member',
        string='Pilot 1',
        required=True,
    )
    pilot1_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P1 Function',
    )

    pilot2_crew_id = fields.Many2one(
        comodel_name='fs.crew.member',
        string='Pilot 2',
    )
    pilot2_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P2 Function',
    )
    mission_id = fields.Many2one(
        comodel_name='fs.flight.mission',
        string='Mission',
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
        help="Standard flight activity (discipline + type) for staff training flights.",
    )
    custom_activity_id = fields.Many2one(
        comodel_name='fs.custom.flight.type',
        string='Custom Activity',
        help="Non-syllabus activity (e.g., test flight, ferry) for staff training.",
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        string='Flight Type',
    )

    route_id = fields.Many2one(
        comodel_name='fs.flight.route',
        string='Route',
    )
    training_class_id = fields.Many2one('fs.training.class', string='Class')
    class_type_id = fields.Many2one('fs.class.type', string='Class Type')
    aircraft_type_id = fields.Many2one('fs.aircraft.type', string='Assigned Aircraft Type')
    is_exam = fields.Boolean(
        string='Is Exam',
        compute='_compute_is_exam',
    )
    crew_warning = fields.Html(compute='_compute_crew_warning')

    @api.onchange('flight_category')
    def _onchange_flight_category(self):
        """Clear all relevant fields when category changes to ensure data consistency."""
        self.pilot1_crew_id = False
        self.pilot1_function = False
        self.pilot2_crew_id = False
        self.pilot2_function = False
        self.aircraft_id = False
        self.mission_id = False
        self.activity_id = False
        self.custom_activity_id = False
        self.training_class_id = False
        self.aircraft_type_id = False
        self.class_type_id = False

    @api.onchange('pilot1_crew_id')
    def _onchange_pilot1_crew(self):
        """Smart assignment when Pilot 1 crew member is selected."""
        # Clear downstream fields to maintain integrity
        self.pilot2_crew_id = False
        self.pilot2_function = False
        self.aircraft_id = False
        self.mission_id = False
        self.training_class_id = False
        self.aircraft_type_id = False
        self.class_type_id = False

        if self.pilot1_crew_id:
            member_type = self.pilot1_crew_id.member_type  # type: ignore
            if member_type == 'student':
                self.pilot1_function = 'student'
                if self.pilot1_crew_id.enrollment_id:  # type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(
                        self.pilot1_crew_id.enrollment_id)  # type: ignore
                    if enrollment:
                        self.training_class_id = enrollment.training_class_id  # type: ignore
                        self.class_type_id = enrollment.training_class_id.class_type_id if enrollment.training_class_id else False  # type: ignore
                        self.aircraft_type_id = enrollment.aircraft_type_id  # type: ignore

                        instructor = enrollment.instructor_id  # type: ignore
                        if instructor and not instructor.has_expired_qualification:  # type: ignore
                            crew_member = self.env['fs.crew.member'].search([
                                ('source_model', '=', 'fs.instructor'),
                                ('source_id', '=', instructor.id),
                            ], limit=1)
                            if crew_member:
                                self.pilot2_crew_id = crew_member
                                self.pilot2_function = 'instructor'
            elif member_type == 'instructor':
                self.pilot1_function = 'instructor'
            else:
                self.pilot1_function = 'pilot'

    @api.onchange('pilot2_crew_id')
    def _onchange_pilot2_crew(self):
        """Smart assignment when Pilot 2 crew member is selected."""
        if self.pilot2_crew_id:
            member_type = self.pilot2_crew_id.member_type  # type: ignore
            if member_type == 'student':
                self.pilot2_function = 'student'
            elif member_type == 'instructor':
                self.pilot2_function = 'instructor'
            else:
                self.pilot2_function = 'pilot'

    @api.onchange('mission_id')
    def _onchange_mission_id(self):
        """Update duration and functions from mission."""
        self.route_id = False
        if self.mission_id:
            self.duration = self.mission_id.duration_hours  # type: ignore
            self.flight_type_id = self.mission_id.flight_type_id  # type: ignore
            if self.mission_id.activity_id:  # type: ignore
                self.activity_id = self.mission_id.activity_id  # type: ignore
            if self.mission_id.flight_type_id and self.mission_id.flight_type_id.is_solo:  # type: ignore
                self.pilot1_function = 'solo'
                if self.pilot2_crew_id:
                    self.pilot2_function = 'supervisor'
            else:
                if self.pilot1_crew_id and self.pilot1_crew_id.member_type == 'student':  # type: ignore
                    self.pilot1_function = 'student'
                if self.pilot2_crew_id and self.pilot2_crew_id.member_type == 'instructor':  # type: ignore
                    self.pilot2_function = 'instructor'

    @api.onchange('activity_id')
    def _onchange_activity(self):
        """Handle activity selection: clear custom_activity and update duration."""
        if self.activity_id:
            self.custom_activity_id = False
            if self.activity_id.discipline_id and self.activity_id.discipline_id.default_flight_duration:  # type: ignore
                self.duration = self.activity_id.discipline_id.default_flight_duration  # type: ignore

    @api.onchange('custom_activity_id')
    def _onchange_custom_activity(self):
        """Handle custom activity selection: clear activity_id and update duration."""
        if self.custom_activity_id:
            self.activity_id = False
            self.mission_id = False
            if self.custom_activity_id.default_duration:  # type: ignore
                self.duration = self.custom_activity_id.default_duration  # type: ignore

    @api.depends('mission_id')
    def _compute_is_exam(self):
        for record in self:
            record.is_exam = record.mission_id.is_exam if record.mission_id else False  # type: ignore

    @api.depends('pilot1_crew_id', 'pilot2_crew_id', 'flight_category')
    def _compute_crew_warning(self):
        for record in self:
            warnings = []
            if record.pilot1_crew_id:
                if record.pilot1_crew_id.has_expired_qualification:  # type: ignore
                    # type: ignore
                    warnings.append(
                        f"<strong>{record.pilot1_crew_id.name}</strong> has expired qualifications/medical.")
                if record.flight_category == 'staff_training' and record.pilot1_crew_id.member_type == 'student':  # type: ignore
                    # type: ignore
                    warnings.append(
                        f"<strong>{record.pilot1_crew_id.name}</strong> is a student (Staff Training selected).")

            if record.pilot2_crew_id:
                if record.pilot2_crew_id.has_expired_qualification:  # type: ignore
                    # type: ignore
                    warnings.append(
                        f"<strong>{record.pilot2_crew_id.name}</strong> has expired qualifications/medical.")
                if record.flight_category == 'staff_training' and record.pilot2_crew_id.member_type == 'student':  # type: ignore
                    # type: ignore
                    warnings.append(
                        f"<strong>{record.pilot2_crew_id.name}</strong> is a student (Staff Training selected).")

            if warnings:
                record.crew_warning = "<div class='alert alert-warning p-2 mb-0' role='alert'><i class='fa fa-exclamation-triangle me-2'/>" + \
                    " | ".join(warnings) + "</div>"
            else:
                record.crew_warning = False

    def action_confirm(self):
        """Create ad-hoc flight (fs.flight)."""
        self.ensure_one()

        # Prepare values for flight
        vals = {
            'callsign': self.callsign,
            'date': self.date,
            'scheduled_start': self.start_time,
            'scheduled_duration': self.duration,
            'aircraft_id': self.aircraft_id.id,
            'pilot1_crew_id': self.pilot1_crew_id.id,
            'pilot1_function': self.pilot1_function,
            'pilot2_crew_id': self.pilot2_crew_id.id if self.pilot2_crew_id else False,
            'pilot2_function': self.pilot2_function,
            'flight_category': self.flight_category,
            'flight_type_id': self.flight_type_id.id if self.flight_type_id else False,
            'route_id': self.route_id.id if self.route_id else False,
            'status': 'scheduled',
        }

        # Add mission or activity based on category
        if self.flight_category == 'student_training' and self.mission_id:
            vals['mission_id'] = self.mission_id.id
        elif self.flight_category == 'staff_training':
            if self.activity_id:
                vals['activity_id'] = self.activity_id.id
            elif self.custom_activity_id:
                vals['custom_activity_id'] = self.custom_activity_id.id

        # Create flight directly (Ad-Hoc)
        # We do NOT create a scheduled flight for ad-hoc additions from the Ops Board
        # (unless requested, but "Ad-Hoc" implies execution record).
        # The Scheduler availability logic will check fs.flight table.
        self.env['fs.flight'].create(vals)

        return {'type': 'ir.actions.act_window_close'}


class FsAddSimWizard(FsAddFlightWizard):
    """Wizard for adding new simulator sessions from simulator operations board."""

    _name = 'fs.add.sim.wizard'
    _inherit = ['fs.add.flight.wizard']
    _description = 'Add Simulator Session Wizard'

    callsign = fields.Char(
        string='Callsign',
        required=True,
        default=lambda self: self._get_next_sim_callsign(),
    )

    aircraft_id = fields.Many2one(
        comodel_name='fs.aircraft',
        string='Simulator',
        required=True,
        domain="[('is_airworthy', '=', True), ('category_id.is_simulator', '=', True)]",
    )

    mission_id = fields.Many2one(
        comodel_name='fs.flight.mission',
        string='Mission',
        domain="[('is_sim', '=', True)]",
    )

    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
        domain="[('is_sim', '=', True)]",
        help="Standard simulator activity for staff training.",
    )

    @api.model
    def _get_next_sim_callsign(self):
        """Generate the next available SIM callsign across flight records."""
        return self._get_next_callsign(is_sim=True)
