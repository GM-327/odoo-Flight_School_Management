# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

# Import shared constants from the sibling addon package.
# This path is resolvable by both Odoo and static analyzers in this workspace.
from fs_scheduling.models.fs_flight_mixin import (
    FLIGHT_CATEGORY_SELECTION,
    PILOT_FUNCTION_SELECTION,
)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsFlight(models.Model):
    """Actual flight execution record.

    This model represents the day-of-operations flight. It is usually created
    by 'pushing' a scheduled flight from the scheduling module, but acts as
    an independent record that can be modified during execution.
    """

    _name = 'fs.flight'
    _description = 'Flight'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'fs.flight.mixin']
    _order = 'date desc, scheduled_start asc'

    # === Link to Scheduled Flight (Parent Plan) ===
    scheduled_flight_id = fields.Many2one(
        comodel_name='fs.scheduled.flight',
        string='Scheduled Flight',
        required=False,  # Optional (Ad-Hoc flights)
        ondelete='set null',
        help="Link to the original plan. Changes here do not affect the plan unless synced.",
    )

    # === Constraints ===
    @api.constrains('callsign', 'date')
    def _check_unique_callsign(self):
        """Ensure callsign is unique (except for 'ADD' which is a placeholder)."""
        for record in self:
            if not record.callsign:
                continue
            # Skip validation for 'ADD' callsign as it's a special placeholder
            if record.callsign.upper() == 'ADD':
                continue
            # Check for duplicates
            duplicates = self.search([
                ('callsign', '=ilike', record.callsign),
                ('date', '=', record.date),
                ('id', '!=', record.id),
            ], limit=1)
            if duplicates:
                raise ValidationError(
                    _("Duplicate callsign detected! The callsign '%(callsign)s' is already assigned to another flight on %(date)s. "
                      "Each flight must have a unique callsign.",
                      callsign=record.callsign,
                      date=duplicates.date),
                )

    # === CRUD Overrides ===
    # Note: ADD callsign is preserved on create - conversion happens when opening the form for edit

    def action_open_form(self):
        """Open flight form and auto-assign callsign if it's 'ADD'. Opens the appropriate popup view."""
        self.ensure_one()
        # Auto-convert ADD callsign when opening for edit
        if self.callsign and self.callsign.upper() == 'ADD':
            new_callsign = self._get_next_add_callsign(self.date)
            self.sudo().write({'callsign': new_callsign})

        # Determine which popup form to use based on aircraft category
        is_simulator = self.aircraft_id.category_id.is_simulator if self.aircraft_id else False  # type: ignore
        view_id = self.env.ref('fs_flights.view_fs_sim_popup_form' if is_simulator else 'fs_flights.view_fs_flight_popup_form').id

        return {
            'name': _('Simulator Session') if is_simulator else _('Flight Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.flight',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }

    def action_save_and_close(self):
        """Save the record and close the popup. Used by popup form views."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    # === Primary Data (Duplicated from Schedule for Independence) ===
    callsign = fields.Char(
        string='Callsign',
        required=True,
        tracking=True,
        index='trigram',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        index=True,
    )
    daily_ops_id = fields.Many2one(
        'fs.daily.operations',
        string='Operations Board',
        compute='_compute_daily_ops',
        store=True,
        index=True,
    )
    simulator_ops_id = fields.Many2one(
        'fs.simulator.operations',
        string='Simulator Board',
        compute='_compute_daily_ops',
        store=True,
        index=True,
    )

    @api.depends('date', 'aircraft_id.category_id.is_simulator')
    def _compute_daily_ops(self):
        """Compute link to operations board. Does NOT create boards - that's handled in create/write."""
        # Collect all dates for batch lookup
        non_sim_dates = set()
        sim_dates = set()

        for record in self:
            if not record.date:
                continue
            if record.aircraft_id and record.aircraft_id.category_id and record.aircraft_id.category_id.is_simulator:  # type: ignore
                sim_dates.add(record.date)
            else:
                non_sim_dates.add(record.date)

        # Batch lookup for daily operations
        ops_map = {}
        if non_sim_dates:
            existing_ops = self.env['fs.daily.operations'].search([('date', 'in', list(non_sim_dates))])
            ops_map = {op.date: op for op in existing_ops}  # type: ignore

        # Batch lookup for simulator operations
        sim_ops_map = {}
        if sim_dates:
            existing_sim_ops = self.env['fs.simulator.operations'].search([('date', 'in', list(sim_dates))])
            sim_ops_map = {op.date: op for op in existing_sim_ops}  # type: ignore

        # Assign values (just link, don't create)
        for record in self:
            is_sim = record.aircraft_id and record.aircraft_id.category_id and record.aircraft_id.category_id.is_simulator  # type: ignore
            if is_sim:
                record.daily_ops_id = False
                record.simulator_ops_id = sim_ops_map.get(record.date, False)
            else:
                record.daily_ops_id = ops_map.get(record.date, False)
                record.simulator_ops_id = False

    def _ensure_operations_board(self):
        """Ensure operations board exists for this flight's date. Called from create/write."""
        for record in self:
            if not record.date:
                continue
            is_sim = record.aircraft_id and record.aircraft_id.category_id and record.aircraft_id.category_id.is_simulator  # type: ignore
            if is_sim:
                existing = self.env['fs.simulator.operations'].search([('date', '=', record.date)], limit=1)
                if not existing:
                    self.env['fs.simulator.operations'].create({'date': record.date})
            else:
                existing = self.env['fs.daily.operations'].search([('date', '=', record.date)], limit=1)
                if not existing:
                    self.env['fs.daily.operations'].create({'date': record.date})
    scheduled_start = fields.Float(
        string='Scheduled Start',
        required=True,
        default=8.0,
        help="Planned Departure Time (ETD)",
        aggregator=None,
    )
    scheduled_duration = fields.Float(
        string='Scheduled Duration',
        default=1.0,
        help="Planned Duration Hours",
    )

    # === Resources ===
    aircraft_id = fields.Many2one(
        comodel_name='fs.aircraft',
        string='Aircraft',
        required=True,
        tracking=True,
        domain="[('is_airworthy', '=', True)]",
    )
    aircraft_registration = fields.Char(
        related='aircraft_id.registration',
        store=True,
        string='Aircraft Registration',
    )
    aircraft_type_id = fields.Many2one(
        comodel_name='fs.aircraft.type',
        string='Assigned Aircraft Type',
        help="Student's specifically assigned aircraft type from their enrollment.",
    )

    # === Crew ===
    pilot1_crew_id = fields.Many2one(
        comodel_name='fs.crew.member',
        string='Pilot 1',
        tracking=True,
    )
    pilot1_callsign = fields.Char(
        related='pilot1_crew_id.name',
        store=True,
        string='Pilot 1',
    )
    pilot1_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P1 Function',
    )

    pilot2_crew_id = fields.Many2one(
        comodel_name='fs.crew.member',
        string='Pilot 2',
        tracking=True,
    )
    pilot2_callsign = fields.Char(
        related='pilot2_crew_id.name',
        store=True,
        string='Pilot 2',
    )
    pilot2_function = fields.Selection(
        selection=PILOT_FUNCTION_SELECTION,
        string='P2 Function',
    )

    # === Mission / Route ===
    flight_category = fields.Selection(
        selection=FLIGHT_CATEGORY_SELECTION,
        string='Category',
        default='student_training',
    )

    mission_id = fields.Many2one(
        comodel_name='fs.flight.mission',
        string='Mission',
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
    )
    custom_activity_id = fields.Many2one(
        comodel_name='fs.custom.flight.type',
        string='Custom Activity',
        help="Non-syllabus activity (e.g., test flight, ferry).",
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        string='Flight Type',
    )
    route_id = fields.Many2one(
        comodel_name='fs.flight.route',
        string='Route',
    )
    route_name = fields.Char(
        related='route_id.name',
        string='Route Name',
        store=True,
    )
    activity_display = fields.Char(
        string='Activity',
        compute='_compute_activity_display',
        store=True,
        help="Display value for activity column showing activity/custom_activity code.",
    )

    @api.depends('activity_id', 'activity_id.code', 'custom_activity_id', 'custom_activity_id.code',  # type: ignore
                 'custom_activity_id.name', 'mission_id', 'mission_id.activity_id', 'mission_id.activity_id.code')  # type: ignore
    def _compute_activity_display(self):
        """Compute display value for activity column showing activity/custom_activity code."""
        for record in self:
            if record.mission_id and record.mission_id.activity_id:  # type: ignore
                # For student training: show mission's activity code
                record.activity_display = record.mission_id.activity_id.code or ''  # type: ignore
            elif record.activity_id:
                # For staff training with activity
                record.activity_display = record.activity_id.code or ''  # type: ignore
            elif record.custom_activity_id:
                # For staff training with custom activity
                record.activity_display = record.custom_activity_id.code or record.custom_activity_id.name or ''  # type: ignore
            else:
                record.activity_display = ''

    # === Helpers for Integration ===
    student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Student',
        compute='_compute_student_info',
        store=True,
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Class',
        compute='_compute_student_info',
        store=True,
    )
    class_type_id = fields.Many2one(
        related='training_class_id.class_type_id',
        store=True,
        string='Class Type',
    )
    flight_code = fields.Char(
        string='Flight Code',
        compute='_compute_flight_code',
        store=True,
    )
    is_solo = fields.Boolean(related='flight_type_id.is_solo', store=True)

    # === Onchange Methods ===

    def _get_next_add_callsign(self, reference_date=None):
        """Generate the next available ADD callsign (e.g., ABS7001, ABS7002, etc.)."""
        ICP = self.env['ir.config_parameter'].sudo()
        prefix = str(ICP.get_param('flight_school.mission_callsign_prefix', 'ABS') or 'ABS')
        threshold = int(ICP.get_param('flight_school.first_added_mission_number', '7000'))  # type: ignore

        # Get current year range
        target_date = reference_date or self.date or fields.Date.context_today(self)
        start_year = target_date.replace(month=1, day=1)
        end_year = target_date.replace(month=12, day=31)

        # Search for all flights in the current year with callsigns above threshold
        domain = [
            ('date', '>=', start_year),
            ('date', '<=', end_year),
            ('callsign', '!=', False),
            ('callsign', '!=', 'ADD'),
            ('id', '!=', self.id if self.id else 0),  # Exclude current record
        ]
        flight_data = self.env['fs.flight'].search_read(domain, ['callsign'])

        # Find the maximum callsign number above threshold
        max_num = threshold - 1  # Start from threshold - 1 so first is exactly threshold
        for data in flight_data:
            c = data['callsign']
            if isinstance(c, str) and c.startswith(prefix) and len(c) > len(prefix):
                suffix = c[len(prefix):]
                if suffix.isdigit():
                    val = int(suffix)
                    if val >= threshold and val > max_num:
                        max_num = val

        # Return the next available number
        next_num = max_num + 1
        return f"{prefix}{next_num}"

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

        if self.pilot1_crew_id:
            member_type = self.pilot1_crew_id.member_type  # type: ignore
            if member_type == 'student':
                if self.pilot1_function not in ('student', 'solo'):
                    self.pilot1_function = 'student'
                if self.pilot1_crew_id.enrollment_id:  # type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(self.pilot1_crew_id.enrollment_id)  # type: ignore
                    if enrollment:
                        self.training_class_id = enrollment.training_class_id  # type: ignore
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
            if member_type == 'instructor':
                self.pilot2_function = 'instructor'
            elif member_type == 'student':
                self.pilot2_function = 'student'
            else:
                self.pilot2_function = 'pilot'

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

    @api.onchange('mission_id')
    def _onchange_mission_id(self):
        """Update duration and functions from mission."""
        self.route_id = False
        if self.mission_id:
            self.scheduled_duration = self.mission_id.duration_hours  # type: ignore
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
                self.scheduled_duration = self.activity_id.discipline_id.default_flight_duration  # type: ignore

    @api.onchange('custom_activity_id')
    def _onchange_custom_activity(self):
        """Handle custom activity selection: clear activity_id and update duration."""
        if self.custom_activity_id:
            self.activity_id = False
            self.mission_id = False
            if self.custom_activity_id.default_duration:  # type: ignore
                self.scheduled_duration = self.custom_activity_id.default_duration  # type: ignore

    # === Execution Times ===
    etd = fields.Float(related='scheduled_start', string='ETD', store=True, aggregator=None)  # Alias for view compatibility
    atd = fields.Float(string='ATD', tracking=True, aggregator=None)
    eta = fields.Float(string='ETA', compute='_compute_eta', store=True, aggregator=None)
    ata = fields.Float(string='ATA', tracking=True, aggregator=None)
    actual_duration = fields.Float(string='Actual Duration', compute='_compute_actual_duration', store=True)
    distributed_hours = fields.Float(
        string='Distributed Hours',
        default=0.0,
        copy=False,
        help="Hours already distributed to entities. Used for tracking and corrections.",
    )

    # === Status ===
    status = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='scheduled',
        required=True,
        tracking=True,
    )
    cancellation_reason_id = fields.Many2one('fs.cancellation.reason', string='Cancellation Reason')
    cancellation_code = fields.Char(related='cancellation_reason_id.code', store=True, string='Cancel Code')

    status_display = fields.Char(compute='_compute_status_display', store=True)
    status_color = fields.Integer(compute='_compute_status_color')
    is_exam = fields.Boolean(string='Is Exam', compute='_compute_is_exam', store=True)
    crew_warning = fields.Html(compute='_compute_crew_warning')
    notes = fields.Text(string='Notes')

    # === Computes ===

    @api.depends('mission_id')
    def _compute_is_exam(self):
        for record in self:
            record.is_exam = record.mission_id.is_exam if record.mission_id else False  # type: ignore

    @api.depends(
        'pilot1_crew_id',
        'pilot1_crew_id.name',
        'pilot1_crew_id.member_type',
        'pilot1_crew_id.has_expired_qualification',
        'pilot2_crew_id',
        'pilot2_crew_id.name',
        'pilot2_crew_id.member_type',
        'pilot2_crew_id.has_expired_qualification',
        'flight_category',
    )
    def _compute_crew_warning(self):
        for record in self:
            warnings = []
            if record.pilot1_crew_id:
                if record.pilot1_crew_id.has_expired_qualification:  # type: ignore
                    warnings.append(f"<strong>{record.pilot1_crew_id.name}</strong> has expired qualifications/medical.")  # type: ignore
                if record.flight_category == 'staff_training' and record.pilot1_crew_id.member_type == 'student':  # type: ignore
                    warnings.append(f"<strong>{record.pilot1_crew_id.name}</strong> is a student (Staff Training selected).")  # type: ignore

            if record.pilot2_crew_id:
                if record.pilot2_crew_id.has_expired_qualification:  # type: ignore
                    warnings.append(f"<strong>{record.pilot2_crew_id.name}</strong> has expired qualifications/medical.")  # type: ignore
                if record.flight_category == 'staff_training' and record.pilot2_crew_id.member_type == 'student':  # type: ignore
                    warnings.append(f"<strong>{record.pilot2_crew_id.name}</strong> is a student (Staff Training selected).")  # type: ignore

            if warnings:
                record.crew_warning = "<div class='alert alert-warning p-2 mb-0' role='alert'><i class='fa fa-exclamation-triangle me-2'/>" + " | ".join(warnings) + "</div>"
            else:
                record.crew_warning = False

    @api.depends(
        'pilot1_crew_id',
        'pilot1_crew_id.member_type',
        'pilot1_crew_id.enrollment_id',
    )
    def _compute_student_info(self):
        for record in self:
            if record.pilot1_crew_id and record.pilot1_crew_id.member_type == 'student' and record.pilot1_crew_id.enrollment_id:  # type: ignore
                enrollment = self.env['fs.student.enrollment'].browse(
                    record.pilot1_crew_id.enrollment_id,  # type: ignore
                ).exists()
                record.student_id = enrollment.student_id if enrollment else False  # type: ignore
                record.training_class_id = enrollment.training_class_id if enrollment else False  # type: ignore
            else:
                record.student_id = False
                record.training_class_id = False

    @api.depends('mission_id', 'mission_id.activity_id', 'mission_id.activity_id.code', 'activity_id', 'activity_id.code')
    def _compute_flight_code(self):
        for record in self:
            if record.mission_id and record.mission_id.activity_id:  # type: ignore
                record.flight_code = record.mission_id.activity_id.code  # type: ignore
            elif record.activity_id:  # type: ignore
                record.flight_code = record.activity_id.code  # type: ignore
            else:
                record.flight_code = False

    @api.depends('scheduled_start', 'scheduled_duration')
    def _compute_eta(self):
        for record in self:
            record.eta = record.scheduled_start + (record.scheduled_duration or 0)

    @api.depends('atd', 'ata')
    def _compute_actual_duration(self):
        for record in self:
            if record.atd is not False and record.ata is not False:
                if record.ata >= record.atd:
                    record.actual_duration = record.ata - record.atd
                else:
                    record.actual_duration = (24.0 - record.atd) + record.ata
            else:
                record.actual_duration = 0.0

    @api.depends('status', 'cancellation_code')
    def _compute_status_display(self):
        selection_map = dict(self.env['fs.flight'].fields_get(['status'])['status']['selection'])
        for record in self:
            if record.status == 'cancelled' and record.cancellation_code:
                record.status_display = record.cancellation_code
            else:
                record.status_display = selection_map.get(record.status, record.status)

    @api.depends('status')
    def _compute_status_color(self):
        color_map = {'scheduled': 3, 'in_progress': 4, 'done': 10, 'cancelled': 1}
        for record in self:
            record.status_color = color_map.get(str(record.status), 0)

    # === Actions ===

    def _compute_status_from_times(self):
        """Determine status based on presence of ATD/ATA. Entering times overrides cancellation."""
        if self.atd is not False and self.ata is not False:
            return 'done'
        if self.atd is not False:
            return 'in_progress'
        # Respect 'cancelled' if no execution times are present
        return self.status if self.status == 'cancelled' else 'scheduled'

    @api.onchange('atd', 'ata')
    def _onchange_execution_times(self):
        """Update status preview and force persistence for inline edits.

        The _origin.write() pattern is critical for the operations board because
        it uses a computed Many2many list where standard row-level saving
        often fails to persist unless forced.
        """
        new_status = self._compute_status_from_times()
        was_cancelled = self.status == 'cancelled'

        # 1. Update virtual record for UI feedback
        if was_cancelled and new_status != 'cancelled':
            self.cancellation_reason_id = False
        self.status = new_status

        # 2. Force database persistence if we have an origin record
        if self._origin:
            # We use a dict to capture whatever is in the virtual record
            # We don't use 'if self.atd' because 0.0 (midnight) is a valid value
            vals = {
                'atd': self.atd,
                'ata': self.ata,
                'status': new_status,
            }
            if was_cancelled and new_status != 'cancelled':
                vals['cancellation_reason_id'] = False

            # This triggers our recursion-safe write() method on the real record
            self._origin.write(vals)

    def action_start_flight(self):
        now = fields.Datetime.now()
        current_time = now.hour + now.minute / 60.0
        self.write({'atd': current_time, 'status': 'in_progress'})

    def action_complete_flight(self):
        now = fields.Datetime.now()
        current_time = now.hour + now.minute / 60.0
        self.write({'ata': current_time, 'status': 'done'})

    def action_cancel_flight(self):
        return {
            'name': _('Cancel Flight'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.flight.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_flight_log_id': self.id,
                'dialog_size': 'small',
                'size': 'sm',
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Create flight records and ensure operations boards exist."""
        records = super().create(vals_list)
        records._ensure_operations_board()
        return records

    def write(self, vals):
        """Override write to handle status updates and hour distribution on state changes.

        This method is designed to be recursion-safe and batch-compatible.
        """
        # 1. Handle cross-field status automation
        # Clear times when explicit cancellation occurs
        if vals.get('status') == 'cancelled':
            vals.update({'atd': False, 'ata': False})

        # 2. Capture pre-write state for all records in the set
        old_data = {
            r.id: {
                'status': r.status,
                'distributed_hours': r.distributed_hours,
                'atd': r.atd,
                'ata': r.ata,
            } for r in self
        }

        # 3. Handle automatic status updates from ATD/ATA changes
        if ('atd' in vals or 'ata' in vals) and 'status' not in vals:
            # Note: We don't update vals directly here for the whole set because
            # different records might need different statuses in a batch write.
            # Instead, we'll handle it during the loop if needed, but for common
            # single-record writes, we can optimize.
            if len(self) == 1:
                new_atd = vals.get('atd', self.atd)
                new_ata = vals.get('ata', self.ata)
                computed_status = self.with_context(
                    status=self.status, atd=new_atd, ata=new_ata,
                )._compute_status_from_times_batch()
                if computed_status != self.status:
                    vals['status'] = computed_status
                    if self.status == 'cancelled' and computed_status != 'cancelled':
                        vals['cancellation_reason_id'] = False

        # 4. Perform the actual write
        res = super().write(vals)

        # 4b. Multi-record time updates need a per-record status reconciliation.
        if len(self) > 1 and ('atd' in vals or 'ata' in vals) and 'status' not in vals:
            for record in self:
                computed_status = record._compute_status_from_times()
                if computed_status != record.status:
                    status_vals = {'status': computed_status}
                    if record.status == 'cancelled' and computed_status != 'cancelled':
                        status_vals['cancellation_reason_id'] = False
                    record.write(status_vals)

        # 5. Post-write adjustments (Hour distribution)
        if not self.env.context.get('skip_distribution'):
            for record in self:
                old = old_data.get(record.id, {})
                old_status = old.get('status')
                old_distributed = old.get('distributed_hours', 0.0)

                new_status = record.status
                new_duration = record.actual_duration

                delta = 0.0
                if new_status == 'done':
                    if old_status != 'done':
                        # Just completed: distribute full duration
                        delta = new_duration
                    elif new_duration != old_distributed:
                        # Still done but duration changed: distribute delta
                        delta = new_duration - old_distributed
                elif old_status == 'done':
                    # Was done, now NOT done: subtract all distributed hours
                    delta = -old_distributed

                if delta != 0:
                    record._distribute_hours(delta)
                    # Update distributed_hours directly in DB to avoid recursion
                    self.env.cr.execute(
                        "UPDATE fs_flight SET distributed_hours = %s WHERE id = %s",
                        (record.distributed_hours + delta, record.id),
                    )
                    record.invalidate_recordset(['distributed_hours'])

        # 6. Maintenance: Ensure operations boards exist
        if 'date' in vals or 'aircraft_id' in vals:
            self._ensure_operations_board()

        return res

    def _compute_status_from_times_batch(self):
        """Helper for batch status computation using context or record values."""
        atd = self.env.context.get('atd', self.atd)
        ata = self.env.context.get('ata', self.ata)
        status = self.env.context.get('status', self.status)

        if atd is not False and ata is not False:
            return 'done'
        if atd is not False:
            return 'in_progress'
        return status if status == 'cancelled' else 'scheduled'

    def unlink(self):
        """Override unlink to subtract hours if flight was completed."""
        for record in self:
            if record.status == 'done' and record.distributed_hours > 0:
                record._distribute_hours(-record.distributed_hours)
        return super().unlink()

    def _is_simulator_session(self):
        """Check if this is a simulator session.

        Priority: mission flag > activity flag > aircraft category
        """
        self.ensure_one()
        if self.mission_id and hasattr(self.mission_id, 'is_sim') and self.mission_id.is_sim:  # type: ignore
            return True
        if self.activity_id and hasattr(self.activity_id, 'is_sim') and self.activity_id.is_sim:  # type: ignore
            return True
        if self.aircraft_id and self.aircraft_id.category_id:  # type: ignore
            return self.aircraft_id.category_id.is_simulator  # type: ignore
        return False

    def _get_person_from_crew(self, crew):
        """Get the actual person record from crew member.

        Uses member_type to determine correct model since the SQL view
        has inconsistent source_model for students.
        """
        if not crew or not crew.source_id:
            return False

        # Map member_type to actual person model
        model_map = {
            'student': 'fs.student',
            'instructor': 'fs.instructor',
            'pilot': 'fs.pilot',
        }
        model = model_map.get(crew.member_type)
        if not model or model not in self.env:
            return False

        return self.env[model].browse(crew.source_id).exists()

    def _get_pilot_function_config(self, function_code):
        """Get pilot function configuration by code.

        Returns dict with is_counted_flight, is_counted_instructor, is_counted_solo.
        """
        if not function_code:
            return {'is_counted_flight': False, 'is_counted_instructor': False, 'is_counted_solo': False}

        PilotFunction = self.env['fs.pilot.function']
        func = PilotFunction.get_function_by_code(function_code)  # type: ignore
        if func:
            return {
                'is_counted_flight': func.is_counted_flight,
                'is_counted_instructor': func.is_counted_instructor,
                'is_counted_solo': func.is_counted_solo,
            }
        # Fallback defaults if function not configured
        return {'is_counted_flight': True, 'is_counted_instructor': False, 'is_counted_solo': False}

    def _distribute_hours(self, hours_delta):
        """Distribute flight hours to Aircraft, Instructor, Pilot, and Student.

        Args:
            hours_delta: Hours to add (positive) or subtract (negative).
        """
        self.ensure_one()
        if hours_delta == 0:
            return

        is_sim = self._is_simulator_session()
        today = fields.Date.context_today(self)

        # 1. Update Aircraft
        if self.aircraft_id:
            aircraft = self.aircraft_id
            vals = {}
            vals['total_hours'] = aircraft.total_hours + hours_delta  # type: ignore
            if hours_delta > 0:
                vals['last_flight_date'] = today
            aircraft.sudo().write(vals)

        # 2. Update Crew members (P1 and P2)
        for crew_attr, func_attr in [('pilot1_crew_id', 'pilot1_function'),
                                      ('pilot2_crew_id', 'pilot2_function')]:
            crew = getattr(self, crew_attr, False)
            func_code = getattr(self, func_attr, False)
            if not crew:
                continue

            person = self._get_person_from_crew(crew)
            if not person:
                continue

            func_config = self._get_pilot_function_config(func_code)
            vals = {}

            if hours_delta > 0:
                vals['last_flight_date'] = today

            if is_sim:
                # Simulator hours tracked separately
                if hasattr(person, 'total_sim_hours'):
                    vals['total_sim_hours'] = person.total_sim_hours + hours_delta  # type: ignore
            else:
                # Flight hours
                if func_config['is_counted_flight'] and hasattr(person, 'total_flight_hours'):
                    vals['total_flight_hours'] = person.total_flight_hours + hours_delta  # type: ignore
                if func_config['is_counted_instructor'] and hasattr(person, 'total_instruction_hours'):
                    vals['total_instruction_hours'] = person.total_instruction_hours + hours_delta  # type: ignore
                if func_config['is_counted_solo'] and hasattr(person, 'solo_hours'):
                    vals['solo_hours'] = person.solo_hours + hours_delta  # type: ignore

            if vals:
                person.sudo().write(vals)

        # 3. Update Student (for student training flights)
        if self.flight_category == 'student_training' and self.student_id:
            student = self.student_id
            vals = {}

            if hours_delta > 0:
                vals['last_flight_date'] = today

            if is_sim:
                vals['total_sim_hours'] = student.total_sim_hours + hours_delta  # type: ignore
            else:
                vals['total_flight_hours'] = student.total_flight_hours + hours_delta  # type: ignore
                # Check P1 function for solo
                p1_func = self._get_pilot_function_config(self.pilot1_function)
                if p1_func['is_counted_solo']:
                    vals['solo_hours'] = student.solo_hours + hours_delta  # type: ignore

            if vals:
                student.sudo().write(vals)

            # Update enrollment activity hours
            self._update_enrollment_hours(hours_delta)

        # 4. Log the distribution
        if hours_delta > 0:
            hours_str = f"{int(hours_delta)}:{int((hours_delta % 1) * 60):02d}"
            self.message_post(  # type: ignore
                body=f"✅ Flight completed. {hours_str} hours distributed.",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )
        elif hours_delta < 0:
            hours_str = f"{int(abs(hours_delta))}:{int((abs(hours_delta) % 1) * 60):02d}"
            self.message_post(  # type: ignore
                body=f"⚠️ Hours adjusted. {hours_str} hours subtracted.",
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def _update_enrollment_hours(self, hours_delta):
        """Update student enrollment activity hours.

        Args:
            hours_delta: Hours to add (positive) or subtract (negative).
        """
        self.ensure_one()
        if not self.student_id or not self.training_class_id:
            return

        enrollment = self.env['fs.student.enrollment'].search([
            ('student_id', '=', self.student_id.id),
            ('training_class_id', '=', self.training_class_id.id),
            ('status', '=', 'active'),
        ], limit=1)

        if not enrollment:
            return

        # Get activity from mission or direct activity
        activity = None
        if self.mission_id and self.mission_id.activity_id:  # type: ignore
            activity = self.mission_id.activity_id  # type: ignore
        elif self.activity_id:
            activity = self.activity_id

        if not activity:
            return

        EnrollmentHours = self.env['fs.enrollment.hours']
        rec = EnrollmentHours.search([
            ('enrollment_id', '=', enrollment.id),
            ('activity_id', '=', activity.id),
        ], limit=1)

        if rec:
            new_hours = max(0, rec.hours_logged + hours_delta)  # type: ignore
            rec.sudo().write({'hours_logged': new_hours})
        elif hours_delta > 0:
            # Only create new record for positive hours
            EnrollmentHours.sudo().create({
                'enrollment_id': enrollment.id,
                'activity_id': activity.id,
                'hours_logged': hours_delta,
                'is_extra': True,
            })

    @api.depends('callsign')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.callsign or _("New Flight")

    def action_delete_flight(self):
        """Delete the flight."""
        self.ensure_one()
        if self.status == 'done':
            raise UserError(_("You cannot delete a completed flight."))

        return {
            'name': _('Confirm Deletion'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.flight.delete.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_flight_log_id': self.id,
                'dialog_size': 'small',
                'size': 'sm',
            },
        }
