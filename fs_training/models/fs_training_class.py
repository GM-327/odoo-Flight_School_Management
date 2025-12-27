# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import date, timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fs_class_type import FsClassType
    from .fs_admin_task import FsAdminTask, FsClassTypeAdminTask


class FsTrainingClass(models.Model):
    """Training class instances."""

    _name = 'fs.training.class'
    _description = 'Training Class'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'expected_end_date, name'

    name = fields.Char(
        string='Class Name',
        required=True,
        tracking=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        copy=False,
        tracking=True,
        help="Short reference code (e.g., CPL24). This code is used as a prefix for all student callsigns in this class (e.g., CPL24A).",
    )
    class_type_id: 'FsClassType' = fields.Many2one( # type: ignore[assignment]
        comodel_name='fs.class.type',
        string='Class Type',
        required=True,
        tracking=True,
        ondelete='restrict',
    )  
    is_military = fields.Boolean(
        string='Military Class',
        related='class_type_id.is_military',
        store=True,
    )
    for_licensed_personnel = fields.Boolean(
        string='For Licensed Personnel',
        related='class_type_id.for_licensed_personnel',
        store=True,
    )
    color = fields.Integer(
        string='Color',
        related='class_type_id.color',
        store=True,
    )

    # === Dates ===
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
    )
    initial_end_date = fields.Date(
        string='Initial End Date',
        compute='_compute_initial_end_date',
        store=True,
        help="Computed from start date + class type duration.",
    )
    expected_end_date = fields.Date(
        string='Expected End Date',
        tracking=True,
        help="For monitoring. Can be extended. Initially = initial end date.",
    )
    actual_end_date = fields.Date(
        string='Actual End Date',
        tracking=True,
        help="Required when completing or cancelling.",
    )

    # === Warnings ===
    end_date_warning_level = fields.Selection(
        selection=[
            ('none', 'None'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ],
        string='End Date Warning Level',
        compute='_compute_end_date_warning',
    )
    end_date_warning_message = fields.Char(
        string='End Date Warning Message',
        compute='_compute_end_date_warning',
    )

    # === Status ===
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        group_expand='_read_group_status',
    )
    status_color = fields.Integer(
        string='Status Color',
        compute='_compute_status_color',
    )

    # === Resources ===
    aircraft_type_ids = fields.Many2many(
        comodel_name='fs.aircraft.type',
        relation='fs_training_class_aircraft_type_rel',
        column1='training_class_id',
        column2='aircraft_type_id',
        string='Aircraft Types',
    )

    # === Enrollments ===
    enrollment_ids = fields.One2many(
        comodel_name='fs.student.enrollment',
        inverse_name='training_class_id',
        string='Enrollments',
    )
    student_count = fields.Integer(
        string='Students',
        compute='_compute_student_counts',
        store=True,
    )
    graduated_count = fields.Integer(
        string='Graduated',
        compute='_compute_student_counts',
        store=True,
    )
    dropped_count = fields.Integer(
        string='Dropped',
        compute='_compute_student_counts',
        store=True,
    )

    # === Admin Tasks ===
    admin_task_ids = fields.One2many(
        comodel_name='fs.admin.task',
        inverse_name='training_class_id',
        string='Admin Tasks',
    )

    # === Progress ===
    progress_percentage = fields.Float(
        string='Progress (%)',
        compute='_compute_progress_percentage',
        store=True,
        help="Average student progression.",
    )

    notes = fields.Text(
        string='Notes',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Class name must be unique!',
    )

    @api.constrains('start_date', 'expected_end_date', 'actual_end_date')
    def _check_dates(self):
        """Ensure end dates are not before start date."""
        for record in self:
            if record.start_date:
                if record.expected_end_date and record.expected_end_date < record.start_date:
                    raise ValidationError("Expected End Date cannot be before Start Date.")
                if record.actual_end_date and record.actual_end_date < record.start_date:
                    raise ValidationError("Actual End Date cannot be before Start Date.")

    @api.depends('start_date', 'class_type_id.duration_value', 'class_type_id.duration_unit')
    def _compute_initial_end_date(self):
        for record in self:
            class_type = record.class_type_id
            if record.start_date and class_type and class_type.duration_value:
                unit = class_type.duration_unit
                if unit == 'weeks':
                    record.initial_end_date = record.start_date + timedelta(weeks=class_type.duration_value)
                elif unit == 'months':
                    # Simplified month addition: 30 days per month
                    record.initial_end_date = record.start_date + timedelta(days=class_type.duration_value * 30)
                else:
                    record.initial_end_date = False
            else:
                record.initial_end_date = False

    @api.depends('expected_end_date', 'status')
    def _compute_end_date_warning(self):
        """Compute end date warning level and message based on config."""
        today = date.today()
        # Get warning days from config
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param('flight_school.class_end_warning_days', '14'))  # type: ignore[attr-defined]
        
        for record in self:
            level = 'none'
            message = False
            
            if record.status == 'in_progress' and record.expected_end_date:
                days_left = (record.expected_end_date - today).days
                
                if days_left < 0:
                    level = 'danger'
                    message = "This class is OVERDUE! The expected end date was %s." % fields.Date.to_string(record.expected_end_date)
                elif days_left <= warning_days:
                    level = 'warning'
                    message = "This class is nearing its expected end date (%s days remaining)." % days_left
            
            record.end_date_warning_level = level
            record.end_date_warning_message = message

    @api.model
    def _read_group_status(self, stages, domain):
        """Ensure status columns (except cancelled) are visible in Kanban even if empty."""
        return [key for key, val in self.fields_get(['status'])['status']['selection'] if key != 'cancelled']

    @api.depends('status')
    def _compute_status_color(self):
        color_map = {
            'draft': 0,
            'in_progress': 4,  # Blue
            'completed': 10,   # Green
            'cancelled': 1,    # Red
        }
        for record in self:
            record.status_color = color_map.get(record.status or 'draft', 0)

    @api.depends('enrollment_ids', 'enrollment_ids.status')
    def _compute_student_counts(self):
        for record in self:
            enrollments = record.enrollment_ids
            record.student_count = len(enrollments)
            record.graduated_count = len(enrollments.filtered_domain([('status', '=', 'graduated')]))
            record.dropped_count = len(enrollments.filtered_domain([('status', '=', 'dropped')]))

    @api.depends('enrollment_ids.progression')
    def _compute_progress_percentage(self):
        for record in self:
            progressions = record.enrollment_ids.mapped('progression')
            if progressions:
                record.progress_percentage = sum(progressions) / len(progressions)
            else:
                record.progress_percentage = 0.0

    @api.onchange('class_type_id')
    def _onchange_class_type_id(self):
        """Copy aircraft types and admin tasks from class type."""
        if self.class_type_id:
            self.aircraft_type_ids = self.class_type_id.aircraft_type_ids
            # Populate admin tasks from templates if no tasks exist yet
            if not self.admin_task_ids:
                new_tasks = []
                for line in self.class_type_id.admin_task_ids:
                    new_tasks.append((0, 0, {
                        'name': line.template_id.name,  # type: ignore
                        'sequence': line.sequence,      # type: ignore
                        'description': line.template_id.description,  # type: ignore
                        'notes': line.notes,             # type: ignore
                    }))
                self.admin_task_ids = new_tasks 

    @api.onchange('initial_end_date')
    def _onchange_initial_end_date(self):
        """Set expected end date to initial if not set."""
        if self.initial_end_date and not self.expected_end_date:
            self.expected_end_date = self.initial_end_date

    @api.model_create_multi
    def create(self, vals_list):
        """Create admin tasks from templates."""
        records = super().create(vals_list)
        for record in records:
            # Create admin tasks from templates ONLY if none were provided via onchange/vals
            if not record.admin_task_ids and record.class_type_id and record.class_type_id.admin_task_ids:
                for task_link in record.class_type_id.admin_task_ids:
                    template = task_link.template_id  # type: ignore
                    self.env['fs.admin.task'].create({
                        'name': template.name,  # type: ignore
                        'training_class_id': record.id,
                        'sequence': task_link.sequence,  # type: ignore
                        'description': template.description,  # type: ignore
                        'notes': task_link.notes,         # type: ignore
                    })
            # Set expected_end_date if not set
            if record.initial_end_date and not record.expected_end_date:
                record.expected_end_date = record.initial_end_date
        return records

    def write(self, vals):
        """Handle status transitions and archiving side effects."""
        # Detect status changes for side effects
        new_status = vals.get('status')
        today = fields.Date.context_today(self)

        for record in self:
            if new_status and new_status != record.status:
                # 1. Moving to In Progress (Start Class)
                if new_status == 'in_progress':
                    record.enrollment_ids.filtered_domain([('status', '=', 'enrolled')]).write({'status': 'active'})
                
                # 2. Moving to Completed (Set End Date)
                elif new_status == 'completed':
                    if not vals.get('actual_end_date') and not record.actual_end_date:
                        vals['actual_end_date'] = today
                    # Graduate students if not already done
                    active_enrollments = record.enrollment_ids.filtered_domain([
                        ('status', 'not in', ['dropped', 'graduated'])
                    ])
                    active_enrollments.write({
                        'status': 'graduated',
                        'graduation_date': today,
                    })
                
                # 3. Moving to Cancelled
                elif new_status == 'cancelled':
                    if not vals.get('actual_end_date') and not record.actual_end_date:
                        vals['actual_end_date'] = today
                    record.enrollment_ids.filtered_domain([
                        ('status', 'in', ['enrolled', 'active'])
                    ]).write({'status': 'cancelled'})

                # 4. Moving back to Draft
                elif new_status == 'draft':
                    vals['actual_end_date'] = False
                    record.enrollment_ids.filtered_domain([('status', '=', 'active')]).write({'status': 'enrolled'})

        result = super().write(vals)
        
        # Original Archive logic
        if 'active' in vals and not vals['active']:
            for record in self:
                students = record.enrollment_ids.mapped('student_id')
                if students:
                    students.write({'active': False})  # type: ignore
        return result

    def action_start_class(self):
        """Start the training class."""
        for record in self:
            if record.status != 'draft':
                raise ValidationError("Only draft classes can be started.")
            record.status = 'in_progress'
            # Update enrollment statuses
            record.enrollment_ids.filtered_domain([('status', '=', 'enrolled')]).write({'status': 'active'})

    def action_set_draft(self):
        """Reset the training class to draft status."""
        for record in self:
            if record.status not in ('in_progress', 'cancelled', 'completed'):
                raise ValidationError("Only in-progress, cancelled or completed classes can be set to draft.")
            record.status = 'draft'
            record.actual_end_date = False
            # Revert active enrollments back to enrolled
            record.enrollment_ids.filtered_domain([('status', '=', 'active')]).write({'status': 'enrolled'})

    def action_complete_class(self):
        """Complete the training class."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.status != 'in_progress':
                raise ValidationError("Only in-progress classes can be completed.")
            if not record.actual_end_date:
                raise ValidationError("Please set the actual end date before completing.")
            
            # Check for students with low progression and log warning
            active_enrollments = record.enrollment_ids.filtered_domain([
                ('status', 'not in', ['dropped', 'graduated'])
            ])
            low_progression = active_enrollments.filtered(lambda e: e.progression < 100)  # type: ignore[attr-defined]
            if low_progression:
                warning_msg = "<b>⚠️ Low Progression Warning:</b><br/>The following students have not completed 100% of their requirements:<ul>"
                for enrollment in low_progression:
                    warning_msg += f"<li>{enrollment.student_id.name}: {enrollment.progression:.1f}%</li>"  # type: ignore
                warning_msg += "</ul>"
                record.message_post(body=warning_msg, message_type='notification')  # type: ignore[attr-defined]
            
            record.status = 'completed'
            # Graduate all active enrollments (not dropped) and set graduation date
            active_enrollments.write({
                'status': 'graduated',
                'graduation_date': today,
            })

    def action_cancel_class(self):
        """Cancel the training class."""
        for record in self:
            if record.status == 'cancelled':
                raise ValidationError("This class is already cancelled.")
            if not record.actual_end_date:
                raise ValidationError("Please set the actual end date before cancelling.")
            record.status = 'cancelled'
            # Set all active/enrolled enrollments to cancelled
            record.enrollment_ids.filtered_domain([
                ('status', 'in', ['enrolled', 'active'])
            ]).write({'status': 'cancelled'})
