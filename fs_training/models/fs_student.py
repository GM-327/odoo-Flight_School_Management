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
        search='_search_is_available_for_enrollment',
        help="True if student has no active or enrolled status in any class.",
    )

    def _compute_is_available_for_enrollment(self):
        """Check if student is available for new enrollment."""
        for record in self:
            active_count = self.env['fs.student.enrollment'].search_count([
                ('student_id', '=', record.id),
                ('status', 'in', ['enrolled', 'active']),
            ])
            record.is_available_for_enrollment = active_count == 0

    def _search_is_available_for_enrollment(self, operator, value):
        """Search method for is_available_for_enrollment field.
        
        Returns a domain to filter students based on their enrollment status.
        A student is 'available' if they have no active/enrolled status in any class.
        """
        # Get all students who have active/enrolled enrollments
        enrollments = self.env['fs.student.enrollment'].search([
            ('status', 'in', ['enrolled', 'active']),
        ])
        enrolled_student_ids = list(enrollments.mapped('student_id').ids)  # type: ignore
        
        # Determine what we're looking for
        # operator='=' value=True means "give me available students"
        # operator='=' value=False means "give me unavailable students"
        looking_for_available = (operator == '=' and value) or (operator == '!=' and not value)
        
        if looking_for_available:
            # We want students who are NOT in the enrolled list
            if enrolled_student_ids:
                return [('id', 'not in', enrolled_student_ids)]
            else:
                # No one is enrolled, so EVERYONE is available
                # Return a domain that matches all records (id > 0)
                return [('id', '>', 0)]
        else:
            # We want students who ARE in the enrolled list
            if enrolled_student_ids:
                return [('id', 'in', enrolled_student_ids)]
            else:
                # No one is enrolled, so NO ONE is unavailable
                # Return a domain that matches no records
                return [('id', '=', 0)]
