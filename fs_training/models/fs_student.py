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
        help="The code of the training class the student is currently enrolled in.",
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
            else:
                record.callsign = False
                record.current_class_code = False

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
