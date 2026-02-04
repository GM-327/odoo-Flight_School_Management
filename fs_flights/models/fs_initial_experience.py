# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsInitialExperience(models.Model):
    """Track initial/prior experience hours for personnel.
    
    This model allows recording flight experience that personnel had before
    being added to the system. These hours are included in total calculations.
    """
    _name = 'fs.initial.experience'
    _description = 'Initial Experience'
    _order = 'entry_date desc, id desc'

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
    )
    
    # === Target Selection ===
    person_type = fields.Selection([
        ('instructor', 'Instructor'),
        ('pilot', 'Pilot'),
        ('student', 'Student'),
    ], string='Person Type', required=True)
    
    instructor_id = fields.Many2one(
        'fs.instructor',
        string='Instructor',
    )
    pilot_id = fields.Many2one(
        'fs.pilot',
        string='Pilot',
    )
    student_id = fields.Many2one(
        'fs.student',
        string='Student',
    )
    
    # === Experience Hours ===
    initial_flight_hours = fields.Float(
        string='Initial Flight Hours',
        help="Prior flight hours before joining.",
    )
    initial_sim_hours = fields.Float(
        string='Initial Sim Hours',
        help="Prior simulator hours before joining.",
    )
    initial_solo_hours = fields.Float(
        string='Initial Solo Hours',
        help="Prior solo flight hours before joining.",
    )
    initial_instruction_hours = fields.Float(
        string='Initial Instruction Hours',
        help="Prior instruction hours (instructors only).",
    )
    
    # === Metadata ===
    entry_date = fields.Date(
        string='Entry Date',
        default=fields.Date.context_today,
        required=True,
        help="Date when this initial experience was recorded.",
    )
    source = fields.Char(
        string='Source',
        help="Source of this experience data (e.g., 'Previous logbook', 'Transfer from other school').",
    )
    notes = fields.Text(string='Notes')
    is_applied = fields.Boolean(
        string='Applied',
        default=False,
        help="If checked, these hours have been added to the person's totals.",
    )
    applied_date = fields.Date(
        string='Applied Date',
        readonly=True,
    )

    @api.depends('person_type', 'instructor_id', 'pilot_id', 'student_id', 'entry_date')
    def _compute_name(self):
        for record in self:
            person_name = ''
            if record.person_type == 'instructor' and record.instructor_id:
                person_name = record.instructor_id.name
            elif record.person_type == 'pilot' and record.pilot_id:
                person_name = record.pilot_id.name
            elif record.person_type == 'student' and record.student_id:
                person_name = record.student_id.name
            record.name = f"{person_name} - {record.entry_date or 'Draft'}"

    @api.onchange('person_type')
    def _onchange_person_type(self):
        """Clear irrelevant person fields when type changes."""
        if self.person_type != 'instructor':
            self.instructor_id = False
            self.initial_instruction_hours = 0
        if self.person_type != 'pilot':
            self.pilot_id = False
        if self.person_type != 'student':
            self.student_id = False

    def action_apply_experience(self):
        """Apply the initial experience hours to the person's totals."""
        for record in self:
            if record.is_applied:
                continue
            
            person = None
            if record.person_type == 'instructor' and record.instructor_id:
                person = record.instructor_id
            elif record.person_type == 'pilot' and record.pilot_id:
                person = record.pilot_id
            elif record.person_type == 'student' and record.student_id:
                person = record.student_id
            
            if not person:
                continue
            
            vals = {}
            if record.initial_flight_hours:
                vals['total_flight_hours'] = person.total_flight_hours + record.initial_flight_hours
            if record.initial_sim_hours and hasattr(person, 'total_sim_hours'):
                vals['total_sim_hours'] = person.total_sim_hours + record.initial_sim_hours
            if record.initial_solo_hours and hasattr(person, 'solo_hours'):
                vals['solo_hours'] = person.solo_hours + record.initial_solo_hours
            if record.initial_instruction_hours and hasattr(person, 'total_instruction_hours'):
                vals['total_instruction_hours'] = person.total_instruction_hours + record.initial_instruction_hours
            
            if vals:
                person.sudo().write(vals)
                record.write({
                    'is_applied': True,
                    'applied_date': fields.Date.context_today(self),
                })
                person.message_post(
                    body=f"📊 Initial experience applied: {record.initial_flight_hours or 0:.1f}h flight, {record.initial_sim_hours or 0:.1f}h sim, {record.initial_solo_hours or 0:.1f}h solo.",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )

    def action_unapply_experience(self):
        """Revert the initial experience hours from the person's totals."""
        for record in self:
            if not record.is_applied:
                continue
            
            person = None
            if record.person_type == 'instructor' and record.instructor_id:
                person = record.instructor_id
            elif record.person_type == 'pilot' and record.pilot_id:
                person = record.pilot_id
            elif record.person_type == 'student' and record.student_id:
                person = record.student_id
            
            if not person:
                continue
            
            vals = {}
            if record.initial_flight_hours:
                vals['total_flight_hours'] = max(0, person.total_flight_hours - record.initial_flight_hours)
            if record.initial_sim_hours and hasattr(person, 'total_sim_hours'):
                vals['total_sim_hours'] = max(0, person.total_sim_hours - record.initial_sim_hours)
            if record.initial_solo_hours and hasattr(person, 'solo_hours'):
                vals['solo_hours'] = max(0, person.solo_hours - record.initial_solo_hours)
            if record.initial_instruction_hours and hasattr(person, 'total_instruction_hours'):
                vals['total_instruction_hours'] = max(0, person.total_instruction_hours - record.initial_instruction_hours)
            
            if vals:
                person.sudo().write(vals)
                record.write({
                    'is_applied': False,
                    'applied_date': False,
                })
