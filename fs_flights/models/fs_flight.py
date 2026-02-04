# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class FsFlight(models.Model):
    """Actual flight execution record.
    
    This model represents the day-of-operations flight. It is usually created
    by 'pushing' a scheduled flight from the scheduling module, but acts as 
    an independent record that can be modified during execution.
    """

    _name = 'fs.flight'
    _description = 'Flight'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, scheduled_start asc'

    # === Link to Scheduled Flight (Parent Plan) ===
    scheduled_flight_id = fields.Many2one(
        comodel_name='fs.scheduled.flight',
        string='Scheduled Flight',
        required=False, # Optional (Ad-Hoc flights)
        ondelete='set null',
        help="Link to the original plan. Changes here do not affect the plan unless synced."
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
                ('id', '!=', record.id),
            ], limit=1)
            if duplicates:
                raise ValidationError(
                    _("Duplicate callsign detected! The callsign '%(callsign)s' is already assigned to another flight on %(date)s. "
                      "Each flight must have a unique callsign.",
                      callsign=record.callsign,
                      date=duplicates.date)
                )

    # === CRUD Overrides ===
    # Note: ADD callsign is preserved on create - conversion happens when opening the form for edit

    def action_open_form(self):
        """Open flight form and auto-assign callsign if it's 'ADD'."""
        self.ensure_one()
        # Auto-convert ADD callsign when opening for edit
        if self.callsign and self.callsign.upper() == 'ADD':
            new_callsign = self._get_next_add_callsign()
            self.sudo().write({'callsign': new_callsign})
        return {
            'name': _('Flight Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.flight',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

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
        # Separate flights into simulator and non-simulator
        non_sim_flights = self.filtered(lambda r: r.date and not r.aircraft_id.category_id.is_simulator)  # type: ignore
        sim_flights = self.filtered(lambda r: r.date and r.aircraft_id.category_id.is_simulator)  # type: ignore
        
        # Handle non-simulator flights -> daily_ops_id
        non_sim_dates = {rec.date for rec in non_sim_flights}
        ops_map = {}
        if non_sim_dates:
            existing_ops = self.env['fs.daily.operations'].search([('date', 'in', list(non_sim_dates))])
            ops_map = {op.date: op for op in existing_ops}  # type: ignore
            missing_dates = non_sim_dates - set(ops_map.keys())
            for d in missing_dates:
                op = self.env['fs.daily.operations'].search([('date', '=', d)], limit=1)
                if not op:
                    op = self.env['fs.daily.operations'].create({'date': d})
                ops_map[d] = op

        # Handle simulator flights -> simulator_ops_id
        sim_dates = {rec.date for rec in sim_flights}
        sim_ops_map = {}
        if sim_dates:
            existing_sim_ops = self.env['fs.simulator.operations'].search([('date', 'in', list(sim_dates))])
            sim_ops_map = {op.date: op for op in existing_sim_ops}  # type: ignore
            missing_sim_dates = sim_dates - set(sim_ops_map.keys())
            for d in missing_sim_dates:
                op = self.env['fs.simulator.operations'].search([('date', '=', d)], limit=1)
                if not op:
                    op = self.env['fs.simulator.operations'].create({'date': d})
                sim_ops_map[d] = op

        # Assign values
        for record in self:
            if record.aircraft_id.category_id.is_simulator:  # type: ignore
                record.daily_ops_id = False
                record.simulator_ops_id = sim_ops_map.get(record.date, False)
            else:
                record.daily_ops_id = ops_map.get(record.date, False)
                record.simulator_ops_id = False
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
    pilot1_function = fields.Selection([
        ('student', 'Student'),
        ('solo', 'Solo'),
        ('instructor', 'Instructor'),
        ('safety_pilot', 'Safety Pilot'),
        ('supervisor', 'Supervisor'),
        ('pilot', 'Pilot'),
    ], string='P1 Function')

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
    pilot2_function = fields.Selection([
        ('student', 'Student'),
        ('solo', 'Solo'),
        ('instructor', 'Instructor'),
        ('safety_pilot', 'Safety Pilot'),
        ('supervisor', 'Supervisor'),
        ('pilot', 'Pilot'),
    ], string='P2 Function')

    # === Mission / Route ===
    flight_category = fields.Selection([
        ('student_training', '📚 Student Training'),
        ('staff_training', '👥 Pilot/Staff Training'),
    ], string='Category', default='student_training')

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
        string='Class Type'
    )
    flight_code = fields.Char(
        string='Flight Code',
        compute='_compute_flight_code',
        store=True,
    )
    is_solo = fields.Boolean(related='flight_type_id.is_solo', store=True)

    # === Onchange Methods ===

    def _get_next_add_callsign(self):
        """Generate the next available ADD callsign (e.g., ABS7001, ABS7002, etc.)."""
        ICP = self.env['ir.config_parameter'].sudo()
        prefix = ICP.get_param('flight_school.mission_callsign_prefix', 'ABS')  # type: ignore
        threshold = int(ICP.get_param('flight_school.first_added_mission_number', '7000'))  # type: ignore
        
        # Get current year range
        today = fields.Date.context_today(self)
        start_year = today.replace(month=1, day=1)
        end_year = today.replace(month=12, day=31)
        
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
        if self.pilot1_crew_id:
            member_type = self.pilot1_crew_id.member_type  # type: ignore
            if member_type == 'student':
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
                                ('source_id', '=', instructor.id)
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
        """Clear fields when category changes."""
        if self.flight_category == 'student_training':
            self.activity_id = False
            self.custom_activity_id = False
        elif self.flight_category == 'staff_training':
            self.mission_id = False

    @api.onchange('mission_id')
    def _onchange_mission_id(self):
        """Update duration and functions from mission."""
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
    etd = fields.Float(related='scheduled_start', string='ETD', store=True, aggregator=None) # Alias for view compatibility
    atd = fields.Float(string='ATD', tracking=True, aggregator=None)
    eta = fields.Float(string='ETA', compute='_compute_eta', store=True, aggregator=None)
    ata = fields.Float(string='ATA', tracking=True, aggregator=None)
    actual_duration = fields.Float(string='Actual Duration', compute='_compute_actual_duration', store=True)

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

    @api.depends('pilot1_crew_id', 'pilot2_crew_id', 'flight_category')
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

    @api.depends('pilot1_crew_id')
    def _compute_student_info(self):
        for record in self:
            if record.pilot1_crew_id and record.pilot1_crew_id.member_type == 'student' and record.pilot1_crew_id.enrollment_id:  # type: ignore
                enrollment = self.env['fs.student.enrollment'].browse(record.pilot1_crew_id.enrollment_id)  # type: ignore
                record.student_id = enrollment.student_id  # type: ignore
                record.training_class_id = enrollment.training_class_id  # type: ignore
            else:
                record.student_id = False
                record.training_class_id = False

    @api.onchange('pilot1_crew_id')
    def _onchange_pilot1_crew_id(self):
        if self.pilot1_crew_id:
            member_type = self.pilot1_crew_id.member_type  # type: ignore
            if member_type == 'student':
                if self.pilot1_function not in ('student', 'solo'):
                    self.pilot1_function = 'student'
                if self.pilot1_crew_id.enrollment_id:  # type: ignore
                    enrollment = self.env['fs.student.enrollment'].browse(self.pilot1_crew_id.enrollment_id)  # type: ignore
                    if enrollment and enrollment.instructor_id:  # type: ignore
                        crew_member = self.env['fs.crew.member'].search([
                            ('source_model', '=', 'fs.instructor'),
                            ('source_id', '=', enrollment.instructor_id.id)  # type: ignore
                        ], limit=1)
                        if crew_member and not self.pilot2_crew_id:
                            self.pilot2_crew_id = crew_member
                            self.pilot2_function = 'instructor'
            elif member_type == 'instructor':
                self.pilot1_function = 'instructor'
            else:
                self.pilot1_function = 'pilot'

    @api.onchange('pilot2_crew_id')
    def _onchange_pilot2_crew_id(self):
        if self.pilot2_crew_id:
            member_type = self.pilot2_crew_id.member_type  # type: ignore
            if member_type == 'student':
                self.pilot2_function = 'student'
            elif member_type == 'instructor':
                self.pilot2_function = 'instructor'
            else:
                self.pilot2_function = 'pilot'

    @api.depends('mission_id', 'activity_id')
    def _compute_flight_code(self):
        for record in self:
            if record.mission_id and record.mission_id.activity_id: # type: ignore
                record.flight_code = record.mission_id.activity_id.code # type: ignore
            elif record.activity_id: # type: ignore
                record.flight_code = record.activity_id.code # type: ignore
            else:
                record.flight_code = False

    @api.depends('scheduled_start', 'scheduled_duration')
    def _compute_eta(self):
        for record in self:
            record.eta = record.scheduled_start + (record.scheduled_duration or 0)

    @api.depends('atd', 'ata')
    def _compute_actual_duration(self):
        for record in self:
            if record.atd and record.ata and record.ata > record.atd:
                record.actual_duration = record.ata - record.atd
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
        """Determine status based on presence of ATD/ATA."""
        if self.status == 'cancelled':
            return self.status
        if self.atd and self.ata:
            return 'done'
        if self.atd:
            return 'in_progress'
        return 'scheduled'

    @api.onchange('atd')
    def _onchange_atd(self):
        self.status = self._compute_status_from_times()
        # Force write if record exists (for immediate UI response)
        if self._origin:
            self._origin.write({'atd': self.atd, 'status': self.status})

    @api.onchange('ata')
    def _onchange_ata(self):
        self.status = self._compute_status_from_times()
        # Force write if record exists (for immediate UI response)
        if self._origin:
            self._origin.write({'ata': self.ata, 'status': self.status})

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

    def write(self, vals):
        # Handle completion logic
        res = super().write(vals)
        for record in self:
            if 'status' in vals and vals['status'] == 'done' and record.actual_duration > 0:
                record._distribute_hours()
        return res

    def _distribute_hours(self):
        """Distribute flight hours to Aircraft and Student."""
        self.ensure_one()
        hours = self.actual_duration
        if hours <= 0: return

        # 1. Update Aircraft
        if self.aircraft_id:
            current = sum(self.aircraft_id.mapped('total_hours'))
            self.aircraft_id.sudo().write({'total_hours': current + hours})

        # 2. Update Student
        if self.flight_category == 'student_training' and self.student_id:
            # Similar logic to fs.flight.log original implementation
            enrollment = self.env['fs.student.enrollment'].search([
                ('student_id', '=', self.student_id.id),
                ('training_class_id', '=', self.training_class_id.id),
                ('status', 'in', ['active', 'solo']),
            ], limit=1)
            
            activity = None
            if self.mission_id and self.mission_id.activity_id: #type:ignore
                activity = self.mission_id.activity_id #type:ignore
            elif self.activity_id:
                activity = self.activity_id
            
            if enrollment and activity:
                EnrollmentHours = self.env['fs.enrollment.hours']
                rec = EnrollmentHours.search([
                    ('enrollment_id', '=', enrollment.id),
                    ('activity_id', '=', activity.id),
                ], limit=1)
                
                if rec:
                    rec.write({'hours_logged': sum(rec.mapped('hours_logged')) + hours})
                else:
                    EnrollmentHours.create({
                        'enrollment_id': enrollment.id,
                        'activity_id': activity.id,
                        'hours_logged': hours,
                        'is_extra': True,
                    })

        # 3. Log
        hours_str = f"{int(hours)}:{int((hours % 1) * 60):02d}"
        self.message_post( # type: ignore
            body=f"✅ Flight completed. {hours_str} hours distributed.",
            message_type='notification',
            subtype_xmlid='mail.mt_note'
        )

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

