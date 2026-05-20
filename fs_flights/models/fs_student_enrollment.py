# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""fs.student.enrollment extensions for prior experience visibility."""
from odoo import _, api, fields, models


class FsStudentEnrollment(models.Model):
    """Expose prior onboarding progression from enrollments."""

    _inherit = 'fs.student.enrollment'

    prior_experience_line_ids = fields.One2many(
        comodel_name='fs.initial.experience.line',
        inverse_name='enrollment_id',
        string='Prior Hour Detail Lines',
        readonly=True,
    )
    prior_syllabus_completion_ids = fields.One2many(
        comodel_name='fs.prior.syllabus.completion',
        inverse_name='enrollment_id',
        string='Prior Syllabus Detail Lines',
        readonly=True,
    )
    prior_experience_line_count = fields.Integer(
        string='Prior Hour Count',
        compute='_compute_prior_experience_counts',
    )
    prior_syllabus_completion_count = fields.Integer(
        string='Prior Syllabus Count',
        compute='_compute_prior_experience_counts',
    )

    @api.depends('prior_experience_line_ids', 'prior_syllabus_completion_ids')
    def _compute_prior_experience_counts(self):
        """Compute prior progression counters."""
        for enrollment in self:
            enrollment.prior_experience_line_count = len(enrollment.prior_experience_line_ids)
            enrollment.prior_syllabus_completion_count = len(enrollment.prior_syllabus_completion_ids)

    def action_view_prior_experience_lines(self):
        """Open prior hour lines for this enrollment."""
        self.ensure_one()
        return {
            'name': _('Prior Hour Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.initial.experience.line',
            'view_mode': 'list,form',
            'domain': [('enrollment_id', '=', self.id)],
            'context': {'default_enrollment_id': self.id},
        }

    def action_view_prior_syllabus_completions(self):
        """Open prior syllabus completion lines for this enrollment."""
        self.ensure_one()
        return {
            'name': _('Prior Syllabus Completions'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.prior.syllabus.completion',
            'view_mode': 'list,form',
            'domain': [('enrollment_id', '=', self.id)],
            'context': {'default_enrollment_id': self.id},
        }
