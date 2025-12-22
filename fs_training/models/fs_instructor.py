# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsInstructor(models.Model):
    """Extend instructor model with training-specific student assignment logic."""
    
    _inherit = 'fs.instructor'  # type: ignore

    enrollment_ids = fields.One2many(
        comodel_name='fs.student.enrollment',
        inverse_name='instructor_id',
        string='Enrollments',
    )
    assigned_student_count = fields.Integer(
        string='Assigned Students',
        compute='_compute_assigned_student_count',
        help="Number of active students currently assigned to this instructor.",
    )
    student_capacity_reached = fields.Boolean(
        string='Capacity Reached',
        compute='_compute_assigned_student_count',
        help="True if the instructor has reached their maximum student limit.",
    )

    @api.depends('max_students', 'enrollment_ids.status')
    def _compute_assigned_student_count(self):
        """Compute count of active students assigned to this instructor."""
        for record in self:
            count = len(record.enrollment_ids.filtered(lambda e: e.status == 'active'))
            record.assigned_student_count = count
            record.student_capacity_reached = count >= record.max_students

    def action_view_assigned_students(self):
        """Open list of active students assigned to this instructor."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Students assigned to {self.display_name}',
            'res_model': 'fs.student.enrollment',
            'view_mode': 'list,form',
            'domain': [('instructor_id', '=', self.id), ('status', '=', 'active')],
            'context': {'default_instructor_id': self.id},
        }
