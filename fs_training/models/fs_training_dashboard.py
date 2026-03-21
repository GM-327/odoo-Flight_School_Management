# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import date
import json
from odoo import api, fields, models


class FsTrainingDashboard(models.TransientModel):
    """Dashboard for Training module - provides KPIs and quick actions.
    
    Uses TransientModel to create temporary records in database.
    Records are automatically cleaned up by Odoo's garbage collection.
    """

    _name = 'fs.training.dashboard'
    _description = 'Training Dashboard'

    name = fields.Char(string='Name', default='Training Dashboard')

    # === Graph Data ===
    class_distribution = fields.Text(
        string='Class Distribution Graph',
        compute='_compute_class_graph_data',
    )

    # === Summary KPIs ===
    enrolment_total = fields.Integer(
        string='Total Enrollments',
        compute='_compute_summary_kpis',
    )
    class_progression = fields.Float(
        string='Overall Progression (%)',
        compute='_compute_summary_kpis',
    )

    # === Training Class KPIs ===
    class_total = fields.Integer(
        string='Total Classes',
        compute='_compute_class_kpis',
    )
    class_draft = fields.Integer(
        string='Draft Classes',
        compute='_compute_class_kpis',
    )
    class_in_progress = fields.Integer(
        string='In Progress',
        compute='_compute_class_kpis',
    )
    class_overdue = fields.Integer(
        string='Overdue Classes',
        compute='_compute_class_kpis',
    )

    # === Enrollment KPIs ===
    enrollment_active = fields.Integer(
        string='Active Students',
        compute='_compute_enrollment_kpis',
    )
    enrollment_enrolled = fields.Integer(
        string='Enrolled (Pending)',
        compute='_compute_enrollment_kpis',
    )

    # === Admin Task KPIs ===
    admin_tasks_pending = fields.Integer(
        string='Pending Admin Tasks',
        compute='_compute_admin_task_kpis',
    )
    admin_tasks_overdue = fields.Integer(
        string='Overdue Admin Tasks',
        compute='_compute_admin_task_kpis',
    )

    def _compute_class_kpis(self):
        """Compute training class statistics."""
        TrainingClass = self.env['fs.training.class']
        today = date.today()
        for record in self:
            record.class_total = TrainingClass.search_count([
                ('status', 'in', ['draft', 'in_progress']),
            ])
            record.class_draft = TrainingClass.search_count([
                ('status', '=', 'draft'),
            ])
            record.class_in_progress = TrainingClass.search_count([
                ('status', '=', 'in_progress'),
            ])
            # Overdue = in progress and past expected end date
            record.class_overdue = TrainingClass.search_count([
                ('status', '=', 'in_progress'),
                ('expected_end_date', '<', today),
            ])

    def _compute_enrollment_kpis(self):
        """Compute student enrollment statistics."""
        Enrollment = self.env['fs.student.enrollment']
        for record in self:
            record.enrollment_active = Enrollment.search_count([
                ('status', '=', 'active'),
            ])
            record.enrollment_enrolled = Enrollment.search_count([
                ('status', '=', 'enrolled'),
            ])

    def _compute_summary_kpis(self):
        """Compute top-level summary statistics."""
        Enrollment = self.env['fs.student.enrollment']
        Class = self.env['fs.training.class']
        for record in self:
            record.enrolment_total = Enrollment.search_count([])
            classes = Class.search([('status', '=', 'in_progress')])
            if classes:
                record.class_progression = sum(classes.mapped('progress_percentage')) / len(classes)
            else:
                record.class_progression = 0.0

    def _compute_admin_task_kpis(self):
        """Compute admin task statistics."""
        AdminTask = self.env['fs.admin.task']
        for record in self:
            record.admin_tasks_pending = AdminTask.search_count([
                ('is_done', '=', False),
            ])
            # Admin tasks don't have a due_date field, so we show 0 for overdue
            # In the future, a due_date field could be added to fs.admin.task
            record.admin_tasks_overdue = 0

    def _compute_class_graph_data(self):
        """Compute training class distribution graph data."""
        Class = self.env['fs.training.class']
        data = [
            {'label': 'Draft', 'value': Class.search_count([('status', '=', 'draft')]), 'type': 'future'},
            {'label': 'In Progress', 'value': Class.search_count([('status', '=', 'in_progress')]), 'type': 'future'},
            {'label': 'Finished', 'value': Class.search_count([('status', '=', 'finished')]), 'type': 'past'},
            {'label': 'Cancelled', 'value': Class.search_count([('status', '=', 'cancelled')]), 'type': 'past'},
        ]
        for record in self:
            record.class_distribution = json.dumps([{
                'values': data,
                'key': 'Classes by Status',
            }])

    # === Action Methods ===
    def action_view_classes(self):
        """Open training classes list."""
        return {
            'name': 'Training Classes',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.training.class',
            'view_mode': 'kanban,list,form',
        }

    def action_view_classes_draft(self):
        """Open draft training classes."""
        return {
            'name': 'Draft Classes',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.training.class',
            'view_mode': 'list,kanban,form',
            'domain': [('status', '=', 'draft')],
        }

    def action_view_classes_in_progress(self):
        """Open in-progress training classes."""
        return {
            'name': 'In Progress Classes',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.training.class',
            'view_mode': 'list,kanban,form',
            'domain': [('status', '=', 'in_progress')],
        }

    def action_view_classes_overdue(self):
        """Open overdue training classes."""
        today = date.today()
        return {
            'name': 'Overdue Classes',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.training.class',
            'view_mode': 'list,form',
            'domain': [
                ('status', '=', 'in_progress'),
                ('expected_end_date', '<', today),
            ],
        }

    def action_view_enrollments_active(self):
        """Open active enrollments."""
        return {
            'name': 'Active Students',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student.enrollment',
            'view_mode': 'list,kanban,form',
            'domain': [('status', '=', 'active')],
        }

    def action_view_enrollments_enrolled(self):
        """Open pending enrollments."""
        return {
            'name': 'Enrolled (Pending Start)',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student.enrollment',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'enrolled')],
        }

    def action_view_admin_tasks_pending(self):
        """Open pending admin tasks."""
        return {
            'name': 'Pending Admin Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.admin.task',
            'view_mode': 'list,form',
            'domain': [('is_done', '=', False)],
        }

    def action_view_admin_tasks_overdue(self):
        """Open pending admin tasks (no due_date field available)."""
        return {
            'name': 'Pending Admin Tasks',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.admin.task',
            'view_mode': 'list,form',
            'domain': [('is_done', '=', False)],
        }
