# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import math
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class FsScheduledFlight(models.Model):
    """Instances of flight missions scheduled for specific resources and times."""

    _name = 'fs.scheduled.flight'
    _description = 'Scheduled Flight'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_datetime desc, callsign'

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

    # === Resources ===
    enrollment_id = fields.Many2one(
        comodel_name='fs.student.enrollment',
        string='Enrollment',
        ondelete='restrict',
        tracking=True,
    )
    student_id = fields.Many2one(
        comodel_name='fs.student',
        related='enrollment_id.student_id',
        store=True,
        readonly=True,
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        related='enrollment_id.training_class_id',
        store=True,
        readonly=True,
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
        ondelete='restrict',
        tracking=True,
    )
    instructor2_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Second Instructor/Pilot',
        ondelete='restrict',
        tracking=True,
    )
    aircraft_id = fields.Many2one(
        comodel_name='fs.aircraft',
        string='Aircraft',
        required=True,
        ondelete='restrict',
        tracking=True,
    )
    aircraft_registration = fields.Char(
        related='aircraft_id.registration',
        string='Aircraft Registration',
        store=True,
    )

    # === Mission Details ===
    mission_id = fields.Many2one(
        comodel_name='fs.flight.mission',
        string='Syllabus Mission',
        ondelete='restrict',
        tracking=True,
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
        help="Non-syllabus activity (e.g. test flight).",
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
    is_solo = fields.Boolean(
        string='Solo Flight',
        default=False,
    )

    # === Execution (for future Flights module) ===
    actual_start = fields.Datetime(string='Actual Start')
    actual_end = fields.Datetime(string='Actual End')
    actual_duration = fields.Float(
        string='Actual Duration',
        compute='_compute_actual_duration',
        store=True,
        readonly=False,
    )

    # === Status ===
    status = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('confirmed', 'Confirmed'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='scheduled',
        required=True,
        tracking=True,
    )
    cancellation_reason_id = fields.Many2one(
        comodel_name='fs.cancellation.reason',
        string='Cancellation Reason',
        ondelete='restrict',
    )
    notes = fields.Text(string='Notes')

    # === Constraints & Validation ===

    @api.constrains('instructor_id', 'start_datetime', 'end_datetime')
    def _check_instructor_conflict(self):
        for record in self:
            if not record.instructor_id or record.status == 'cancelled':
                continue
            conflict = self.search([
                ('id', '!=', record.id),
                ('status', '!=', 'cancelled'),
                ('instructor_id', '=', record.instructor_id.id),
                ('start_datetime', '<', record.end_datetime),
                ('end_datetime', '>', record.start_datetime),
            ])
            if conflict:
                # Based on user feedback: "but without blocking the possibility to make the conflict. use a danger popup confirmation"
                # In Odoo, constraints block. To allow override, we might need a wizard or a warning in UI.
                # However, for now, I'll log a warning or keep it as a constraint but maybe we can use a warning elsewhere.
                # Since the user explicitly asked NOT to block, I will NOT use a hard ValidationError here.
                # I'll use it as a return message or a notification. 
                # Note: Constraints always block the save. I will remove this from constrains and use it in a specialized check.
                pass

    @api.constrains('aircraft_id', 'start_datetime', 'end_datetime')
    def _check_aircraft_conflict(self):
        # Similar logic as instructor conflict - non-blocking as per user request.
        pass

    @api.onchange('enrollment_id')
    def _onchange_enrollment_suggest(self):
        """Set default instructor and suggest next mission."""
        if self.enrollment_id:
            self.instructor_id = self.enrollment_id.instructor_id
            # Mission suggestion logic would go here in a more advanced implementation

    @api.onchange('mission_id')
    def _onchange_mission_id(self):
        if self.mission_id:
            self.duration = self.mission_id.duration_hours
            self.custom_activity_id = False

    @api.onchange('custom_activity_id')
    def _onchange_custom_activity(self):
        if self.custom_activity_id:
            self.duration = self.custom_activity_id.default_duration
            self.mission_id = False

    # === Computes ===

    @api.depends('start_time', 'duration')
    def _compute_end_time(self):
        for record in self:
            record.end_time = record.start_time + record.duration

    @api.depends('date', 'start_time', 'end_time')
    def _compute_datetimes(self):
        for record in self:
            if record.date:
                # Convert float time (8.5) to hours and minutes
                start_hour = int(record.start_time)
                start_min = int(round((record.start_time - start_hour) * 60))
                
                end_hour = int(record.end_time)
                end_min = int(round((record.end_time - end_hour) * 60))
                
                base_dt = datetime.combine(record.date, datetime.min.time())
                record.start_datetime = base_dt + timedelta(hours=start_hour, minutes=start_min)
                record.end_datetime = base_dt + timedelta(hours=end_hour, minutes=end_min)

    @api.depends('mission_id', 'custom_activity_id')
    def _compute_discipline(self):
        for record in self:
            if record.mission_id:
                record.discipline_id = record.mission_id.discipline_id
            else:
                record.discipline_id = False

    @api.depends('actual_start', 'actual_end')
    def _compute_actual_duration(self):
        for record in self:
            if record.actual_start and record.actual_end:
                diff = record.actual_end - record.actual_start
                record.actual_duration = diff.total_seconds() / 3600.0

    # === Helpers ===

    def _default_date(self):
        """Default to next working day (Mon-Fri)."""
        today = fields.Date.context_today(self)
        next_day = today + timedelta(days=1)
        # 5 = Saturday, 6 = Sunday
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('callsign') or vals.get('callsign') == '/':
                vals['callsign'] = self._generate_next_callsign(vals.get('date'))
        return super().create(vals_list)

    def _generate_next_callsign(self, date=False):
        """Generate next callsign based on prefix and sequence."""
        prefix = self.env['ir.config_parameter'].sudo().get_param('flight_school.mission_callsign_prefix', 'ABS')
        # Simple sequence logic: find max today and increment
        # In a real production system, ir.sequence would be better but requires more setup.
        # I'll use a simplified search-based generation.
        last = self.search([('callsign', '=like', f'{prefix}%')], order='callsign desc', limit=1)
        if last and last.callsign and last.callsign[len(prefix):].isdigit():
            num = int(last.callsign[len(prefix):]) + 1
        else:
            num = 1
        return f"{prefix}{num:04d}"

    def action_confirm(self):
        self.write({'status': 'confirmed'})

    def action_cancel(self):
        # Open a wizard for cancellation reason would be better, but simple for now
        self.write({'status': 'cancelled'})

    def check_conflicts(self):
        """Check for resource conflicts with 15-min buffer. Returns warning list."""
        self.ensure_one()
        if not self.start_datetime or not self.end_datetime or self.status == 'cancelled':
            return []

        buffer_min = int(self.env['ir.config_parameter'].sudo().get_param('flight_school.scheduling_buffer_minutes', '15'))
        buffer = timedelta(minutes=buffer_min)
        
        start_with_buffer = self.start_datetime - buffer
        end_with_buffer = self.end_datetime + buffer

        conflicts = []
        
        # Instructor conflict
        if self.instructor_id:
            i_conflict = self.search([
                ('id', '!=', self.id),
                ('status', '!=', 'cancelled'),
                ('instructor_id', '=', self.instructor_id.id),
                ('start_datetime', '<', end_with_buffer),
                ('end_datetime', '>', start_with_buffer),
            ])
            if i_conflict:
                conflicts.append(_("Instructor %s has another flight overlap (with %d min buffer).") % (self.instructor_id.name, buffer_min))

        # Aircraft conflict
        if self.aircraft_id:
            a_conflict = self.search([
                ('id', '!=', self.id),
                ('status', '!=', 'cancelled'),
                ('aircraft_id', '=', self.aircraft_id.id),
                ('start_datetime', '<', end_with_buffer),
                ('end_datetime', '>', start_with_buffer),
            ])
            if a_conflict:
                conflicts.append(_("Aircraft %s has another flight overlap (with %d min buffer).") % (self.aircraft_id.registration, buffer_min))

        return conflicts
