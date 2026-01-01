# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta, datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FsSchedulingWizard(models.TransientModel):
    """Wizard for batch scheduling of flight missions."""

    _name = 'fs.scheduling.wizard'
    _description = 'Scheduling Wizard'

    def _default_date(self):
        today = fields.Date.context_today(self)
        next_day = today + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        return next_day

    date = fields.Date(
        string='Scheduling Date',
        required=True,
        default=_default_date,
    )
    callsign_prefix = fields.Char(
        string='Callsign Prefix',
        default=lambda self: self.env['ir.config_parameter'].sudo().get_param('flight_school.mission_callsign_prefix', 'ABS'),  # type: ignore
    )
    next_callsign_number = fields.Integer(
        string='Next Flight Number',
        compute='_compute_next_callsign_number',
        readonly=True,
    )
    
    line_ids = fields.One2many(
        comodel_name='fs.scheduling.wizard.line',
        inverse_name='wizard_id',
        string='Scheduling Lines',
    )

    @api.depends('callsign_prefix')
    def _compute_next_callsign_number(self):
        prefix = self.callsign_prefix or 'ABS'
        last = self.env['fs.scheduled.flight'].search(
            [('callsign', '=like', f'{prefix}%')], 
            order='callsign desc', 
            limit=1
        )
        if last and last.callsign and last.callsign[len(prefix):].isdigit():  # type: ignore
            self.next_callsign_number = int(last.callsign[len(prefix):]) + 1  # type: ignore
        else:
            self.next_callsign_number = 1

    @api.onchange('date')
    def _onchange_date_load_students(self):
        """Load eligible students who have not yet reached 100% progression."""
        if not self.date:
            return

        # Eligibility check: active enrollment + no expiries
        enrollments = self.env['fs.student.enrollment'].search([
            ('status', '=', 'active'),
            ('progression', '<', 100.0),
            ('has_expired_status', '=', False),
        ])

        lines = []
        for enrollment in enrollments:
            # Basic mission suggestion: first incomplete mission in sequence
            mission = enrollment.training_class_id.class_type_id.flight_mission_ids.filtered( # type: ignore
                lambda m: not m.is_extra
            )[:1] # Simplified: just pick the first one for now

            lines.append((0, 0, {
                'enrollment_id': enrollment.id,
                'instructor_id': enrollment.instructor_id.id, # type: ignore
                'mission_id': mission.id if mission else False,
                'duration': mission.duration_hours if mission else 1.0,
            }))
        self.line_ids = lines

    def action_schedule(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No students selected for scheduling."))

        scheduled_flights = self.env['fs.scheduled.flight']
        prefix = self.callsign_prefix or 'ABS'
        next_num = self.next_callsign_number

        # Sort lines by some logic if needed, e.g. instructor or student
        for line in self.line_ids:
            # Determine start time (simplified sequential for now)
            # In a real UX, we'd have a better time picker in the wizard lines
            start_time = 8.0 # Default starting at 8:00 AM
            
            callsign = f"{prefix}{next_num:04d}"
            
            scheduled_flights.create({
                'callsign': callsign,
                'date': self.date,
                'start_time': line.start_time or start_time,  # type: ignore
                'duration': line.duration,  # type: ignore
                'enrollment_id': line.enrollment_id.id,  # type: ignore
                'instructor_id': line.instructor_id.id,  # type: ignore
                'aircraft_id': line.aircraft_id.id,  # type: ignore
                'mission_id': line.mission_id.id,  # type: ignore
                'is_solo': line.is_solo,  # type: ignore
            })
            next_num += 1

        return {
            'type': 'ir.actions.act_window',
            'name': 'Tomorrow\'s Schedule',
            'res_model': 'fs.scheduled.flight',
            'view_mode': 'timeline,list,form',
            'target': 'current',
            'context': {'search_default_tomorrow': 1},
        }


class FsSchedulingWizardLine(models.TransientModel):
    _name = 'fs.scheduling.wizard.line'
    _description = 'Scheduling Wizard Line'

    wizard_id = fields.Many2one('fs.scheduling.wizard', ondelete='cascade')
    enrollment_id = fields.Many2one('fs.student.enrollment', string='Student/Class', required=True)
    student_id = fields.Many2one(related='enrollment_id.student_id', string='Student')
    instructor_id = fields.Many2one('fs.instructor', string='Instructor')
    aircraft_id = fields.Many2one('fs.aircraft', string='Aircraft', domain=[('is_airworthy', '=', True)])
    mission_id = fields.Many2one('fs.flight.mission', string='Mission')
    duration = fields.Float(string='Duration', default=1.0)
    start_time = fields.Float(string='Start Time', default=8.0)
    is_solo = fields.Boolean(string='Solo')

    @api.onchange('enrollment_id')
    def _onchange_enrollment(self):
        if self.enrollment_id:
            self.instructor_id = self.enrollment_id.instructor_id  # type: ignore
            # Filter aircraft types allowed for this class
            class_rec = self.enrollment_id.training_class_id  # type: ignore
            if class_rec.aircraft_type_ids:
                return {'domain': {'aircraft_id': [
                    ('is_airworthy', '=', True),
                    ('aircraft_type_id', 'in', class_rec.aircraft_type_ids.ids)
                ]}}

    @api.onchange('mission_id')
    def _onchange_mission(self):
        if self.mission_id:
            self.duration = self.mission_id.duration_hours  # type: ignore
            if self.mission_id.is_exam:  # type: ignore
                # Filter instructors who are examinators
                return {'domain': {'instructor_id': [('qualification_ids.qualification_id.is_examinator', '=', True)]}}
