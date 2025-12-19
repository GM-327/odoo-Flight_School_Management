# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from typing import TYPE_CHECKING, Optional, cast
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

if TYPE_CHECKING:
    from .class_type import FsClassType
    from .student_enrollment import FsStudentEnrollment


class FsTrainingClass(models.Model):
    """Training Class - Batch of students progressing together."""

    _name = 'fs.training.class'
    _description = 'Training Class'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, name'

    # === Basic Info ===
    name = fields.Char(
        string='Class Name',
        required=True,
        tracking=True,
        help="Human-friendly class label, e.g., 'CPL 2024-Alpha'."
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help="Short unique identifier, e.g., 'CPL24A'."
    )
    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Training Program',
        required=True,
        tracking=True,
        help="Training program/type this class follows."
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True,
        help="Planned start date for this class."
    )
    initial_end_date = fields.Date(
        string='Initial End Date',
        compute='_compute_initial_end_date',
        store=True,
        readonly=False,
        tracking=True,
        help="Initial end date based on program duration. Can be adjusted manually when in draft status."
    )
    expected_end_date = fields.Date(
        string='Expected End Date',
        tracking=True,
        help="Estimated end date after extensions. Can be adjusted when class is active."
    )
    end_date_warning = fields.Boolean(
        string='End Date Warning',
        compute='_compute_end_date_warning',
        help="Indicates when the expected end date is within the configured warning window."
    )
    days_until_end = fields.Integer(
        string='Days Until End',
        compute='_compute_days_until_end',
        help="Number of days remaining until the expected end date."
    )
    actual_end_date = fields.Date(
        string='Actual End Date',
        tracking=True,
        help="Date when the class actually finished. Required when marking as completed/cancelled."
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help="Lifecycle status for this training class."
    )
    color = fields.Integer(
        string='Color',
        related='class_type_id.color',
        store=True,
        readonly=True,
        help="Color indicator inherited from the training program."
    )



    enrollment_ids: 'fields.One2many[FsStudentEnrollment]' = fields.One2many(  # type: ignore[assignment]
        comodel_name='fs.student.enrollment',
        inverse_name='training_class_id',
        string='Enrollments'
    )
    student_ids = fields.Many2many(
        comodel_name='fs.student',
        string='Students',
        compute='_compute_students_from_enrollments',
        help="All students linked to this class via enrollments."
    )

    # === Progress Tracking ===
    progress_percentage = fields.Float(
        string='Overall Progress (%)',
        help="Overall completion estimate for this class (0-100)."
    )
    total_flight_hours_logged = fields.Float(
        string='Total Flight Hours',
        compute='_compute_flight_stats',
        store=True,
        help="Sum of all flight hours logged by students in this class."
    )
    average_hours_per_student = fields.Float(
        string='Avg Hours / Student',
        compute='_compute_flight_stats',
        store=True,
        help="Average flight hours per student."
    )

    # === Student Counts ===
    student_count = fields.Integer(
        string='Student Count',
        compute='_compute_student_stats',
        store=True
    )
    active_student_count = fields.Integer(
        string='Active Students',
        compute='_compute_student_stats',
        store=True
    )
    graduated_student_count = fields.Integer(
        string='Graduated Students',
        compute='_compute_student_stats',
        store=True
    )
    dropped_student_count = fields.Integer(
        string='Dropped Students',
        compute='_compute_student_stats',
        store=True
    )

    # === Notes & Admin ===
    notes = fields.Text(string='Notes')
    admin_notes = fields.Text(string='Admin Notes')
    regulation_notes = fields.Text(string='Regulation Notes')
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Uncheck to archive this class."
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The training class code must be unique!'
    )
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'The training class name must be unique!'
    )

    @api.depends('enrollment_ids.student_id')
    def _compute_students_from_enrollments(self):
        for record in self:
            record.student_ids = record.enrollment_ids.mapped('student_id')

    @api.model
    def _get_class_end_warning_days(self):
        """Get the warning threshold days from system parameters."""
        # Remove sudo() - use proper access rights
        param = self.env['ir.config_parameter'].sudo().get_param('flight_school.class_end_warning_days', '14')  # type: ignore[attr-defined]
        try:
            return int(param)
        except (TypeError, ValueError):
            return 14

    @api.depends('expected_end_date', 'status')
    def _compute_end_date_warning(self):
        for record in self:
            record.end_date_warning = record._calculate_end_date_warning()

    @api.depends('expected_end_date')
    def _compute_days_until_end(self):
        """Compute the number of days until the expected end date."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.expected_end_date:
                expected = fields.Date.to_date(record.expected_end_date)
                if expected:
                    delta = expected - today
                    record.days_until_end = max(0, delta.days)
                else:
                    record.days_until_end = 0
            else:
                record.days_until_end = 0

    @api.depends('class_type_id', 'start_date')
    def _compute_initial_end_date(self):
        """Compute initial end date from program duration when in draft status."""
        for record in self:
            if record.start_date and record.class_type_id:
                duration = record.class_type_id.estimated_duration  # type: ignore
                unit = record.class_type_id.estimated_duration_unit or 'months'  # type: ignore
                if duration:
                    start = fields.Date.to_date(record.start_date)
                    if start:
                        delta = relativedelta(months=int(duration)) if unit == 'months' else relativedelta(weeks=int(duration))
                        record.initial_end_date = start + delta
                    else:
                        record.initial_end_date = False
                else:
                    record.initial_end_date = False
            else:
                record.initial_end_date = False

    @api.onchange('expected_end_date', 'status')
    def _onchange_end_date_warning(self):
        """Re-evaluate warning immediately when the expected end date changes in the form."""
        for record in self:
            record.end_date_warning = record._calculate_end_date_warning()

    def _calculate_end_date_warning(self):
        """Return True when expected end date is within the warning window and still open."""
        today = fields.Date.context_today(self)
        warning_days = self._get_class_end_warning_days()
        threshold = today + relativedelta(days=warning_days)
        expected = fields.Date.to_date(self.expected_end_date) if self.expected_end_date else None
        return bool(expected and expected <= threshold and self.status not in ('completed', 'cancelled'))

    # === Computed Display Name ===
    @api.depends('code', 'name')
    def _compute_display_name(self):
        for record in self:
            # show only the class name in relational fields, fall back to code if needed
            record.display_name = record.name or record.code

    # === Onchange Helpers ===
    @api.onchange('initial_end_date')
    def _onchange_initial_end_date(self):
        """Initialize expected end date when initial end date is set."""
        for record in self:
            if record.initial_end_date and not record.expected_end_date:
                record.expected_end_date = record.initial_end_date

    @api.onchange('actual_end_date', 'expected_end_date')
    def _onchange_actual_end_date(self):
        """Warn when the actual end date slips more than 3 months past expected."""
        if self.actual_end_date and self.expected_end_date:
            grace_date = self.expected_end_date + relativedelta(months=3)
            if self.actual_end_date > grace_date:
                return {
                    'warning': {
                        'title': _('Delayed Training'),
                        'message': _('The actual end date is more than 3 months after the expected end date.'),
                    }
                }

    # === Compute Methods ===
    @api.depends('enrollment_ids.status')
    def _compute_student_stats(self):
        """Compute student statistics efficiently using filtered."""
        for record in self:
            enrollments = record.enrollment_ids
            record.student_count = len(enrollments)
            record.active_student_count = len(enrollments.filtered(lambda e: cast('FsStudentEnrollment', e).status == 'active'))
            record.graduated_student_count = len(enrollments.filtered(lambda e: cast('FsStudentEnrollment', e).status == 'graduated'))
            record.dropped_student_count = len(enrollments.filtered(lambda e: cast('FsStudentEnrollment', e).status == 'dropped'))

    @api.depends('enrollment_ids.student_id.total_flight_hours', 'enrollment_ids.student_id')
    def _compute_flight_stats(self):
        for record in self:
            total_hours = sum(record.student_ids.mapped('total_flight_hours'))
            student_count = len(record.student_ids)
            record.total_flight_hours_logged = total_hours
            record.average_hours_per_student = total_hours / student_count if student_count else 0.0

    # === Constraints ===
    @api.constrains('start_date', 'initial_end_date', 'expected_end_date', 'actual_end_date')
    def _check_date_sequence(self):
        """Ensure dates are in proper sequence."""
        for record in self:
            if record.start_date and record.initial_end_date:
                if record.initial_end_date <= record.start_date:
                    raise ValidationError(
                        _('Initial end date must be after the start date for class "%s".') % record.name
                    )
            
            if record.initial_end_date and record.expected_end_date:
                if record.expected_end_date < record.initial_end_date:
                    raise ValidationError(
                        _('Expected end date cannot be before the initial end date for class "%s".') % record.name
                    )
            
            if record.actual_end_date and record.start_date:
                if record.actual_end_date < record.start_date:
                    raise ValidationError(
                        _('Actual end date cannot be before the start date for class "%s".') % record.name
                    )

    # === CRUD Helpers ===
    @api.model_create_multi
    def create(self, vals_list):
        """Autogenerate codes (uppercase) and initialize expected_end_date."""
        for vals in vals_list:
            # Enforce uppercase codes
            if vals.get('code'):
                vals['code'] = vals['code'].upper()
            
            # Initialize expected_end_date from initial_end_date if not provided
            # initial_end_date will be computed automatically
        
        records = super().create(vals_list)
        
        # After creation, set expected_end_date to initial_end_date if not provided
        for record in records:
            if not record.expected_end_date and record.initial_end_date:
                record.expected_end_date = record.initial_end_date
        
        return records

    def write(self, vals):
        """Uppercase code and enforce field protection based on status."""
        vals = vals.copy()
        
        # Enforce uppercase codes
        if vals.get('code'):
            vals['code'] = vals['code'].upper()

        # Validate status transitions and field protection
        locked_statuses = ('completed', 'cancelled')
        status_target = vals.get('status')
        
        # Fields that cannot be edited when status is completed/cancelled
        protected_fields = {
            'name', 'code', 'class_type_id', 'start_date', 
            'initial_end_date', 'enrollment_ids'
        }
        
        # Fields that can be edited only in draft status
        draft_only_fields = {'initial_end_date'}
        
        for record in self:
            # Check if trying to edit protected fields when closed
            if record.status in locked_statuses and status_target not in ('draft', 'active'):
                blocked_fields = protected_fields & set(vals.keys())
                if blocked_fields:
                    labels = [self._fields[f].string or f for f in blocked_fields]
                    raise ValidationError(
                        _('Cannot modify %s while class "%s" is %s. Change status to Draft or Active first.') 
                        % (', '.join(labels), record.name, record.status)
                    )
            
            # Check draft-only field edits
            if record.status != 'draft':
                blocked_draft = (draft_only_fields & set(vals.keys())) - {'expected_end_date'}
                if blocked_draft and 'initial_end_date' in blocked_draft:
                    raise ValidationError(
                        _('Initial end date can only be modified when class "%s" is in Draft status.') % record.name
                    )
        
        # Validate actual_end_date when closing
        if status_target in locked_statuses:
            for record in self:
                if not vals.get('actual_end_date') and not record.actual_end_date:
                    raise ValidationError(
                        _('Please provide an actual end date when marking class "%s" as %s.') 
                        % (record.name, status_target)
                    )
        
        result = super().write(vals)
        
        # Trigger student recomputation when class is completed or cancelled
        if status_target in locked_statuses:
            for record in self:
                # Trigger recomputation of student enrollment data by marking enrollments as modified
                if record.enrollment_ids:
                    record.enrollment_ids.modified(['status'])
        
        return result

    def unlink(self):
        """Archive classes with students instead of deleting."""
        to_delete = self.browse()
        for record in self:
            if record.student_ids:
                record.write({'active': False})
            else:
                to_delete |= record
        if to_delete:
            return super(FsTrainingClass, to_delete).unlink()
        return True



    # === Actions ===
    def action_archive(self):
        self.write({'active': False})

    def action_unarchive(self):
        self.write({'active': True})

    def action_set_draft(self):
        """Set class status to draft."""
        self.write({'status': 'draft'})
    
    def action_activate(self):
        """Activate the training class."""
        self.write({'status': 'active'})
    
    def action_mark_completed(self):
        """Mark class as completed. Requires actual end date."""
        for record in self:
            if not record.actual_end_date:
                raise ValidationError(
                    _('Please set the actual end date before marking class "%s" as completed.') % record.name
                )
            # Auto-update enrollment status to 'graduated' for students still marked as 'active'
            active_enrollments = record.enrollment_ids.filtered(lambda e: cast('FsStudentEnrollment', e).status == 'active')
            if active_enrollments:
                active_enrollments.write({'status': 'graduated'})
        self.write({'status': 'completed'})
    
    def action_cancel(self):
        """Cancel the training class. Requires actual end date."""
        for record in self:
            if not record.actual_end_date:
                raise ValidationError(
                    _('Please set the actual end date before cancelling class "%s".') % record.name
                )
            # Auto-update enrollment status to 'dropped' for students still marked as 'active'
            active_enrollments = record.enrollment_ids.filtered(lambda e: cast('FsStudentEnrollment', e).status == 'active')
            if active_enrollments:
                active_enrollments.write({'status': 'dropped'})
        self.write({'status': 'cancelled'})
    
    def action_view_enrollments(self):
        """Open a view showing enrollments for this class."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Enrollments: %s') % self.name,
            'res_model': 'fs.student.enrollment',
            'view_mode': 'list,form',
            'domain': [('training_class_id', '=', self.id)],
            'context': {'default_training_class_id': self.id},
        }
