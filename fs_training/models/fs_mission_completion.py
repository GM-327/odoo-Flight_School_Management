# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsMissionCompletion(models.Model):
    """Track mission completions per student enrollment.
    
    This model records which missions have been completed during a training
    enrollment, allowing the system to filter available missions and track
    student progress.
    """
    _name = 'fs.mission.completion'
    _description = 'Mission Completion'
    _rec_name = 'mission_id'
    _order = 'completion_date desc, id desc'

    enrollment_id = fields.Many2one(
        'fs.student.enrollment',
        string='Enrollment',
        required=True,
        ondelete='cascade',
        index=True,
    )
    mission_id = fields.Many2one(
        'fs.flight.mission',
        string='Mission',
        required=True,
        ondelete='restrict',
        index=True,
    )
    # Storing ID as integer to avoid circular dependency with fs_flights
    flight_ref_id = fields.Integer(
        string='Flight Reference ID',
        help="ID of the flight where this mission was completed.",
        index=True,
    )
    completion_date = fields.Date(
        string='Completion Date',
        default=fields.Date.context_today,
        required=True,
    )
    notes = fields.Text(string='Notes')

    # Related fields for display
    student_id = fields.Many2one(
        related='enrollment_id.student_id',
        string='Student',
        store=True,
    )
    training_class_id = fields.Many2one(
        related='enrollment_id.training_class_id',
        string='Training Class',
        store=True,
    )
    activity_id = fields.Many2one(
        related='mission_id.activity_id',
        string='Activity',
        store=True,
    )

    _unique_enrollment_mission = models.Constraint(
        'UNIQUE(enrollment_id, mission_id)',
        'This mission has already been marked as completed for this enrollment.'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Log mission completion."""
        records = super().create(vals_list)
        for record in records:
            if record.enrollment_id:
                record.enrollment_id.message_post(
                    body=f"✅ Mission '{record.mission_id.name}' completed on {record.completion_date}.",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )
        return records
