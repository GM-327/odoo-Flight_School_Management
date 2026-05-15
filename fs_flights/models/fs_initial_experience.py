# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Flights fs initial experience module.

Purpose:
    Defines classes FsInitialExperience for daily operations boards, simulator operations, flight execution logs, cancellation workflows, schedule imports, and hour distribution.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from odoo import api, fields, models


class FsInitialExperience(models.Model):
    """Record initial/previous flight experience for people.

    This allows recording hours that were accumulated before the system
    was implemented, or hours from other flight schools/organizations.
    These hours are added to the running totals.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.initial.experience``.
        _description (str): Human-readable model label, ``Initial Experience``.

    Related:
        fs_scheduling provides planned flights.
        fs_training enrollments receive completed-hour updates.
    """
    _name = 'fs.initial.experience'
    _description = 'Initial Experience'
    _order = 'entry_date desc, id desc'
    _rec_name = 'display_name'

    person_type = fields.Selection([
        ('instructor', 'Instructor'),
        ('pilot', 'Pilot'),
        ('student', 'Student'),
    ], string='Person Type', required=True, index=True)

    instructor_id = fields.Many2one(
        'fs.instructor',
        string='Instructor',
        ondelete='cascade',
        index=True,
    )
    pilot_id = fields.Many2one(
        'fs.pilot',
        string='Pilot',
        ondelete='cascade',
        index=True,
    )
    student_id = fields.Many2one(
        'fs.student',
        string='Student',
        ondelete='cascade',
        index=True,
    )

    # Hour fields
    initial_flight_hours = fields.Float(
        string='Flight Hours',
        help="Initial flight hours to add to total.",
    )
    initial_sim_hours = fields.Float(
        string='Simulator Hours',
        help="Initial simulator hours to add to total.",
    )
    initial_solo_hours = fields.Float(
        string='Solo Hours',
        help="Initial solo hours to add to total.",
    )
    initial_instruction_hours = fields.Float(
        string='Instruction Hours',
        help="Initial instruction hours (for instructors only).",
    )

    entry_date = fields.Date(
        string='Entry Date',
        default=fields.Date.context_today,
        required=True,
    )
    description = fields.Char(
        string='Description',
        help="Source of these hours (e.g., Previous employer, Other flight school)",
    )
    notes = fields.Text(
        string='Notes',
    )

    is_applied = fields.Boolean(
        string='Applied',
        default=False,
        help="Whether these hours have been added to the person's totals.",
    )
    applied_date = fields.Datetime(
        string='Applied Date',
    )
    applied_by = fields.Many2one(
        'res.users',
        string='Applied By',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('person_type', 'instructor_id', 'pilot_id', 'student_id', 'entry_date')
    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            person_name = ''
            if record.person_type == 'instructor' and record.instructor_id:
                person_name = record.instructor_id.name
            elif record.person_type == 'pilot' and record.pilot_id:
                person_name = record.pilot_id.name
            elif record.person_type == 'student' and record.student_id:
                person_name = record.student_id.name
            else:
                person_name = 'Unknown'

            date_str = record.entry_date.strftime('%Y-%m-%d') if record.entry_date else ''
            record.display_name = f"{person_name} - {date_str}"

    @api.onchange('person_type')
    def _onchange_person_type(self):
        """Clear irrelevant person fields when type changes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.person_type != 'instructor':
            self.instructor_id = False
            self.initial_instruction_hours = 0.0
        if self.person_type != 'pilot':
            self.pilot_id = False
        if self.person_type != 'student':
            self.student_id = False

    def _get_person(self):
        """Get the linked person record.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        self.ensure_one()
        if self.person_type == 'instructor':
            return self.instructor_id
        elif self.person_type == 'pilot':
            return self.pilot_id
        elif self.person_type == 'student':
            return self.student_id
        return False

    def action_apply_hours(self):
        """Apply the initial hours to the person's totals.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        for record in self:
            if record.is_applied:
                continue

            person = record._get_person()
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
                'applied_date': fields.Datetime.now(),
                'applied_by': self.env.uid,
            })

    def action_revert_hours(self):
        """Revert the initial hours from the person's totals.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        for record in self:
            if not record.is_applied:
                continue

            person = record._get_person()
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
                vals['total_instruction_hours'] = max(
                    0, person.total_instruction_hours - record.initial_instruction_hours)

            if vals:
                person.sudo().write(vals)

            record.write({
                'is_applied': False,
                'applied_date': False,
                'applied_by': False,
            })
