# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FsStudentEnrollment(models.Model):
    """Tracks a student's enrollment history in training classes."""

    _name = 'fs.student.enrollment'
    _description = 'Student Enrollment'
    _order = 'enrollment_date desc'

    student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Student',
        required=True,
        ondelete='cascade',
        index=True
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Training Class',
        required=True,
        ondelete='restrict',
        index=True
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Default Instructor',
        help="The default instructor assigned to this student for this class."
    )
    callsign = fields.Char(
        string='Callsign',
        required=True,
        help="Student callsign for this specific class enrollment."
    )

    enrollment_date = fields.Date(
        string='Enrollment Date',
        related='training_class_id.start_date',
        store=True,
        readonly=True,
        help="Always mirrors the training class start date."
    )
    status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('graduated', 'Graduated'),
            ('dropped', 'Dropped'),
        ],
        string='Status',
        default='active',
        required=True
    )

    _unique_student_class = models.Constraint(
        'unique(student_id, training_class_id)',
        'The student is already enrolled in this class.'
    )
    _unique_class_callsign = models.Constraint(
        'unique(training_class_id, callsign)',
        'This callsign is already taken in this class.'
    )


    @api.constrains('status', 'student_id', 'training_class_id')
    def _check_single_active_enrollment(self):
        """Ensure a student can only have one active enrollment in active/draft classes."""
        for record in self:
            if record.status == 'active':
                # Check if the training class is active or draft
                training_class_status = record.training_class_id.status  # type: ignore
                
                # Only enforce single active enrollment if the class is active or draft
                if training_class_status in ('active', 'draft'):
                    active_count = self.search_count([
                        ('student_id', '=', record.student_id.id),
                        ('status', '=', 'active'),
                        ('training_class_id.status', 'in', ['active', 'draft']),
                        ('id', '!=', record.id)
                    ])
                    if active_count > 0:
                        raise ValidationError(_(
                            "A student can only have one active enrollment in an active or draft training class at a time."
                        ))

    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.student_id.name} - {record.training_class_id.name}"  # type: ignore

    @api.onchange('student_id')
    def _onchange_student_id(self):
        """Set default instructor from student's primary instructor."""
        if self.student_id and self.student_id.primary_instructor_id:  # type: ignore
            self.instructor_id = self.student_id.primary_instructor_id  # type: ignore
        
        # Return domain to filter only available students
        return {
            'domain': {
                'student_id': [
                    '|',
                    ('enrollment_status', '!=', 'active'),
                    ('training_class_id.status', 'in', ['completed', 'cancelled'])
                ]
            }
        }
