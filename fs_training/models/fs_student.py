# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs student module.

Purpose:
    Defines classes FsStudent for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import api, fields, models


class FsStudent(models.Model):
    """Extend student model with training-specific availability logic.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``fs.student``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

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
        compute='_compute_callsign',
        store=True,
        help="Current active enrollment callsign, or the latest valid callsign from enrollment history.",
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
        """Compute the number of classes the student is enrolled in.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.enrollment_count = len(record.enrollment_ids)

    def _get_callsign_enrollment(self):
        """Return the active enrollment, or latest past enrollment with a callsign."""
        self.ensure_one()
        fallback_date = fields.Date.from_string('1970-01-01')
        active_enrollments = self.enrollment_ids.filtered(lambda e: e.status == 'active')
        if active_enrollments:
            candidates = active_enrollments
        else:
            candidates = self.enrollment_ids.filtered(
                lambda e: e.status in ('graduated', 'dropped', 'cancelled') and e.callsign)
        return candidates.sorted(
            lambda e: (e.enrollment_date or fallback_date, e.id),
            reverse=True,
        )[:1]

    @api.depends(
        'enrollment_ids',
        'enrollment_ids.callsign',
        'enrollment_ids.status',
        'enrollment_ids.enrollment_date',
    )
    def _compute_callsign(self):
        """Store the current active callsign, falling back to latest past callsign."""
        for record in self:
            enrollment = record._get_callsign_enrollment()
            record.callsign = enrollment.callsign if enrollment else False

    @api.depends(
        'enrollment_ids',
        'enrollment_ids.callsign',
        'enrollment_ids.training_class_id.code',
        'enrollment_ids.training_class_id.expected_end_date',
        'enrollment_ids.status',
        'enrollment_ids.enrollment_date',
        'enrollment_ids.progression',
        'enrollment_ids.total_hours',
        'enrollment_ids.remaining_hours',
    )
    def _compute_enrollment_data(self):
        """Find callsign and class data from active or latest valid enrollment.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            last_enrollment = record._get_callsign_enrollment()
            if last_enrollment:
                class_rec = getattr(last_enrollment, 'training_class_id', False)
                record.current_class_code = getattr(class_rec, 'code', False) if class_rec else False
                record.enrollment_status = getattr(last_enrollment, 'status', False)
                record.enrollment_progression = getattr(last_enrollment, 'progression', 0.0)
                record.enrollment_total_hours = getattr(last_enrollment, 'total_hours', 0.0)
                record.enrollment_remaining_hours = getattr(last_enrollment, 'remaining_hours', 0.0)
                record.enrollment_expected_end_date = getattr(
                    class_rec, 'expected_end_date', False) if class_rec else False
            else:
                record.current_class_code = False
                record.enrollment_status = False
                record.enrollment_progression = 0.0
                record.enrollment_total_hours = 0.0
                record.enrollment_remaining_hours = 0.0
                record.enrollment_expected_end_date = False

    def action_view_enrolled_classes(self):
        """View the list of enrollments for this student.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
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
        """Check if student is available for new enrollment.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            active_count = self.env['fs.student.enrollment'].sudo().search_count([
                ('student_id', '=', record.id),
                ('status', 'in', ['enrolled', 'active']),
            ])
            record.is_available_for_enrollment = (active_count == 0)
