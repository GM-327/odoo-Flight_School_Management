# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsStudent(models.Model):
    """Extend student model with training-specific availability logic."""
    
    _inherit = 'fs.student'  # type: ignore

    is_available_for_enrollment = fields.Boolean(
        string='Available for Enrollment',
        compute='_compute_is_available_for_enrollment',
        help="True if student has no active or enrolled status in any class.",
    )

    enrollment_ids = fields.One2many(
        comodel_name='fs.student.enrollment',
        inverse_name='student_id',
        string='Enrollments',
    )
    
    callsign = fields.Char(
        string='Callsign',
        compute='_compute_enrollment_data',
        help="The callsign assigned to the student in their most recent training class.",
    )
    current_class_code = fields.Char(
        string='Current Class',
        compute='_compute_enrollment_data',
    )
    enrollment_status = fields.Selection(
        selection=[
            ('enrolled', 'Enrolled'),
            ('active', 'Active'),
            ('graduated', 'Graduated'),
            ('dropped', 'Dropped'),
            ('cancelled', 'Cancelled'),
        ],
        string='Enrollment Status',
        compute='_compute_enrollment_data',
    )
    enrollment_progression = fields.Float(
        string='Progression (%)',
        compute='_compute_enrollment_data',
    )
    enrollment_total_hours = fields.Float(
        string='Logged Hours',
        compute='_compute_enrollment_data',
    )
    enrollment_remaining_hours = fields.Float(
        string='Remaining Hours',
        compute='_compute_enrollment_data',
    )
    enrollment_expected_end_date = fields.Date(
        string='Expected Completion',
        compute='_compute_enrollment_data',
    )
    enrollment_count = fields.Integer(
        string='Classes',
        compute='_compute_enrollment_count',
    )

    def _compute_enrollment_count(self):
        """Compute the number of classes the student is enrolled in."""
        for record in self:
            record.enrollment_count = len(record.enrollment_ids)

    @api.depends('enrollment_ids', 'enrollment_ids.callsign', 'enrollment_ids.training_class_id.code', 'enrollment_ids.status', 'enrollment_ids.enrollment_date')
    def _compute_enrollment_data(self):
        """Find the callsign and class code from the most relevant enrollment (active first, then most recent)."""
        for record in self:
            enrollments = record.enrollment_ids
            if enrollments:
                # Prioritize active enrollments, then enrolled, then others
                # Then sort by date DESC
                sorted_enrollments = enrollments.sorted(
                    lambda e: (
                        1 if getattr(e, 'status', False) == 'active' else (0.5 if getattr(e, 'status', False) == 'enrolled' else 0),
                        getattr(e, 'enrollment_date', fields.Date.from_string('1970-01-01')) or fields.Date.from_string('1970-01-01'),
                        e.id
                    ),
                    reverse=True
                )
                last_enrollment = sorted_enrollments[0]
                record.callsign = getattr(last_enrollment, 'callsign', False)
                class_rec = getattr(last_enrollment, 'training_class_id', False)
                record.current_class_code = getattr(class_rec, 'code', False) if class_rec else False
                record.enrollment_status = getattr(last_enrollment, 'status', False)
                record.enrollment_progression = getattr(last_enrollment, 'progression', 0.0)
                record.enrollment_total_hours = getattr(last_enrollment, 'total_hours', 0.0)
                record.enrollment_remaining_hours = getattr(last_enrollment, 'remaining_hours', 0.0)
                record.enrollment_expected_end_date = getattr(class_rec, 'expected_end_date', False) if class_rec else False
            else:
                record.callsign = False
                record.current_class_code = False
                record.enrollment_status = False
                record.enrollment_progression = 0.0
                record.enrollment_total_hours = 0.0
                record.enrollment_remaining_hours = 0.0
                record.enrollment_expected_end_date = False

    def action_view_enrolled_classes(self):
        """View the list of enrollments for this student."""
        self.ensure_one()
        return {
            'name': 'Enrolled Classes',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student.enrollment',
            'view_mode': 'list,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    @api.depends('enrollment_ids.status')
    def _compute_is_available_for_enrollment(self):
        """Check if student is available for new enrollment."""
        for record in self:
            active_count = self.env['fs.student.enrollment'].sudo().search_count([
                ('student_id', '=', record.id),
                ('status', 'in', ['enrolled', 'active']),
            ])
            record.is_available_for_enrollment = (active_count == 0)
