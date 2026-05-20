# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Smart actions from people roles to prior experience headers."""
from odoo import _, api, fields, models


class FsStudentPriorExperience(models.Model):
    """Add prior-experience access from students."""

    _inherit = 'fs.student'

    prior_experience_count = fields.Integer(
        string='Prior Experience',
        compute='_compute_prior_experience_count',
    )

    @api.depends('name')
    def _compute_prior_experience_count(self):
        grouped = self.env['fs.initial.experience'].read_group(
            [('person_type', '=', 'student'), ('student_id', 'in', self.ids)],
            ['student_id'],
            ['student_id'],
        )
        count_by_student = {
            group['student_id'][0]: group['student_id_count']
            for group in grouped
            if group.get('student_id')
        }
        for student in self:
            student.prior_experience_count = count_by_student.get(student.id, 0)

    def action_view_prior_experience(self):
        self.ensure_one()
        action = self.env.ref('fs_flights.action_fs_initial_experience').read()[0]
        action['name'] = _('Prior Experience')
        action['domain'] = [('person_type', '=', 'student'), ('student_id', '=', self.id)]
        action['context'] = {'default_person_type': 'student', 'default_student_id': self.id}
        return action


class FsPilotPriorExperience(models.Model):
    """Add prior-experience access from pilots."""

    _inherit = 'fs.pilot'

    prior_experience_count = fields.Integer(
        string='Prior Experience',
        compute='_compute_prior_experience_count',
    )

    @api.depends('name')
    def _compute_prior_experience_count(self):
        grouped = self.env['fs.initial.experience'].read_group(
            [('person_type', '=', 'pilot'), ('pilot_id', 'in', self.ids)],
            ['pilot_id'],
            ['pilot_id'],
        )
        count_by_pilot = {
            group['pilot_id'][0]: group['pilot_id_count']
            for group in grouped
            if group.get('pilot_id')
        }
        for pilot in self:
            pilot.prior_experience_count = count_by_pilot.get(pilot.id, 0)

    def action_view_prior_experience(self):
        self.ensure_one()
        action = self.env.ref('fs_flights.action_fs_initial_experience').read()[0]
        action['name'] = _('Prior Experience')
        action['domain'] = [('person_type', '=', 'pilot'), ('pilot_id', '=', self.id)]
        action['context'] = {'default_person_type': 'pilot', 'default_pilot_id': self.id}
        return action


class FsInstructorPriorExperience(models.Model):
    """Add prior-experience access from instructors."""

    _inherit = 'fs.instructor'

    prior_experience_count = fields.Integer(
        string='Prior Experience',
        compute='_compute_prior_experience_count',
    )

    @api.depends('name')
    def _compute_prior_experience_count(self):
        grouped = self.env['fs.initial.experience'].read_group(
            [('person_type', '=', 'instructor'), ('instructor_id', 'in', self.ids)],
            ['instructor_id'],
            ['instructor_id'],
        )
        count_by_instructor = {
            group['instructor_id'][0]: group['instructor_id_count']
            for group in grouped
            if group.get('instructor_id')
        }
        for instructor in self:
            instructor.prior_experience_count = count_by_instructor.get(instructor.id, 0)

    def action_view_prior_experience(self):
        self.ensure_one()
        action = self.env.ref('fs_flights.action_fs_initial_experience').read()[0]
        action['name'] = _('Prior Experience')
        action['domain'] = [('person_type', '=', 'instructor'), ('instructor_id', '=', self.id)]
        action['context'] = {'default_person_type': 'instructor', 'default_instructor_id': self.id}
        return action
