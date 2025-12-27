# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class FsStudentEnrollment(models.Model):
    """Student enrollment in a training class."""

    _name = 'fs.student.enrollment'
    _description = 'Student Enrollment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'training_class_id, student_id'

    _unique_student_class = models.Constraint(
        'UNIQUE(student_id, training_class_id)',
        'This student is already enrolled in this class!',
    )

    student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Student',
        required=True,
        tracking=True,
        ondelete='restrict',
        domain="['!', ('enrollment_ids.status', 'in', ['enrolled', 'active'])]",
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Training Class',
        required=True,
        tracking=True,
        ondelete='cascade',
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Assigned Instructor',
        tracking=True,
        ondelete='restrict',
        domain="[('active', '=', True)]",
        help="Instructor assigned to supervise this student in this class.",
    )
    callsign = fields.Char(
        string='Callsign',
        help="Student's callsign for this class. Auto-suggested as ClassCode + Letter (e.g., CPL24A).",
    )

    @api.onchange('training_class_id', 'student_id')
    def _onchange_student_id_suggest_callsign(self):
        """Suggest a callsign based on class code + incrementing letter.
        Supports batch adding by checking sibling lines in the UI.
        """
        if self.training_class_id and self.training_class_id.code and not self.callsign: # type: ignore
            class_code = self.training_class_id.code # type: ignore
            
            # Count sibling lines (including existing ones and draft ones in the UI)
            # In a One2many context, self.training_class_id.enrollment_ids contains the live list.
            # We count how many callsigns are already set to determine the next letter.
            count = 0
            if self.training_class_id.enrollment_ids: # type: ignore
                # Filter out the current record to avoid double-counting if callsign was already set
                # and count callsigns to find the 'next' slot
                existing_callsigns = self.training_class_id.enrollment_ids.mapped('callsign') # type: ignore
                count = len([c for c in existing_callsigns if c])
            else:
                # Fallback to database search if parent collection is not accessible (e.g. standalone form)
                count = self.env['fs.student.enrollment'].search_count([
                    ('training_class_id', '=', self.training_class_id.id),
                ])
            
            # Generate next letter (A=0, B=1, etc.)
            if count < 26:
                next_letter = chr(ord('A') + count)
            else:
                first_letter = chr(ord('A') + (count // 26) - 1)
                second_letter = chr(ord('A') + (count % 26))
                next_letter = first_letter + second_letter
            
            self.callsign = f"{class_code}{next_letter}"
    status = fields.Selection(
        selection=[
            ('enrolled', 'Enrolled'),
            ('active', 'Active'),
            ('graduated', 'Graduated'),
            ('dropped', 'Dropped'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='enrolled',
        required=True,
        tracking=True,
    )

    @api.onchange('training_class_id')
    def _onchange_training_class_id_set_status(self):
        """Set enrollment status based on class status and populate hour requirements."""
        if self.training_class_id:
            class_rec = self.training_class_id
            class_status = class_rec.status  # type: ignore

            if class_status == 'in_progress':
                self.status = 'active'
            elif class_status == 'draft':
                self.status = 'enrolled'
            
            # Auto-populate hour records from class type requirements
            class_type = class_rec.class_type_id  # type: ignore
            if class_type and class_type.hour_requirement_ids:  # type: ignore
                # Build commands: first clear, then create new records
                commands = [(5, 0, 0)]  # Clear all existing
                for req in class_type.hour_requirement_ids:  # type: ignore
                    commands.append((0, 0, {  # type: ignore
                        'activity_id': req.activity_id.id,
                        'hours_logged': 0.0,
                        'is_extra': False,
                    }))
                self.required_hour_ids = commands  # type: ignore
                self.total_hours = 0.0
            else:
                self.required_hour_ids = [(5, 0, 0)]  # Clear if no requirements found
                self.total_hours = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Final safety net: Populate flight hours if the UI failed to do so."""
        for vals in vals_list:
            # We check if the required_hour_ids commands sent by the UI are valid.
            hour_commands = vals.get('required_hour_ids', [])
            is_valid = False
            if hour_commands:
                for cmd in hour_commands:
                    if isinstance(cmd, (list, tuple)) and cmd[0] == 0:
                        if cmd[2] and cmd[2].get('activity_id'):
                            is_valid = True
                            break
            
            if not is_valid and vals.get('training_class_id'):
                training_class = self.env['fs.training.class'].browse(vals['training_class_id'])
                class_type = training_class.class_type_id # type: ignore
                if class_type and class_type.hour_requirement_ids:
                    commands = [(5, 0, 0)]
                    for req in class_type.hour_requirement_ids:
                        commands.append((0, 0, { # type: ignore
                            'activity_id': req.activity_id.id,
                            'hours_logged': 0.0,
                            'is_extra': False,
                        }))
                    vals['required_hour_ids'] = commands
        return super().create(vals_list)

    @api.onchange('required_hour_ids', 'extra_hour_ids')
    def _onchange_hours_recompute_totals(self):
        """Force real-time recalculation of total hours and progress in the UI."""
        total = sum(self.required_hour_ids.mapped('hours_logged')) + \
                sum(self.extra_hour_ids.mapped('hours_logged'))
        self.total_hours = total
        
        if self.training_class_id and self.training_class_id.class_type_id: # type: ignore
            reqs = self.training_class_id.class_type_id.hour_requirement_ids # type: ignore
            total_req = sum(reqs.mapped('minimum_hours'))
            if total_req > 0:
                total_progress = 0.0
                for req in reqs:
                    logged = sum(self.required_hour_ids.filtered(
                        lambda h: h.activity_id == req.activity_id
                    ).mapped('hours_logged'))
                    # Cap progression per activity at 100%
                    total_progress += min(logged, req.minimum_hours)
                self.progression = (total_progress / total_req) * 100.0
            else:
                self.progression = 100.0 if total > 0 else 0.0

    is_active = fields.Boolean(
        string='Is Active',
        compute='_compute_is_active',
        store=True,
    )

    # === Date Tracking ===
    enrollment_date = fields.Date(
        string='Enrollment Date',
        related='training_class_id.start_date',
        store=True,
        help="Date when the student was enrolled (class start date).",
    )
    graduation_date = fields.Date(
        string='Graduation Date',
        tracking=True,
        help="Date when the student graduated.",
    )
    drop_date = fields.Date(
        string='Drop Date',
        tracking=True,
        help="Date when the student was dropped.",
    )
    required_hour_ids = fields.One2many(
        comodel_name='fs.enrollment.hours',
        inverse_name='enrollment_id',
        string='Required Hours',
        domain=[('is_extra', '=', False)],
    )
    extra_hour_ids = fields.One2many(
        comodel_name='fs.enrollment.hours',
        inverse_name='enrollment_id',
        string='Extra Hours',
        domain=[('is_extra', '=', True)],
    )

    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
        store=True,
    )

    progression = fields.Float(
        string='Progression (%)',
        compute='_compute_progression',
        store=True,
        aggregator='avg',
        help="Percentage of minimum hours completed.",
    )
    notes = fields.Text(
        string='Notes',
    )

    # Related fields for display
    class_status = fields.Selection(
        string='Class Status',
        related='training_class_id.status',
        store=True,
    )
    student_name = fields.Char(
        string='Student Name',
        related='student_id.name',
        store=True,
    )
    medical_status = fields.Selection(
        related='student_id.medical_status',
        string='Medical Status',
    )
    license_expiry_status = fields.Selection(
        related='student_id.license_expiry_status',
        string='License Status',
    )
    security_clearance_status = fields.Selection(
        related='student_id.security_clearance_status',
        string='Security Status',
    )
    insurance_status = fields.Selection(
        related='student_id.insurance_status',
        string='Insurance Status',
    )
    student_image = fields.Image(
        related='student_id.image_128',
        string='Student Image',
    )
    student_phone = fields.Char(
        related='student_id.phone',
        string='Phone',
    )
    has_expired_status = fields.Boolean(
        related='student_id.has_expired_status',
        string='Has Expired Status',
    )
    remaining_hours = fields.Float(
        string='Remaining Syllabus Hours',
        compute='_compute_remaining_hours',
        help="Total hours remaining to complete the mandatory syllabus requirements.",
    )
    remaining_breakdown_html = fields.Html(
        string='Remaining Breakdown',
        compute='_compute_remaining_breakdown_html',
    )

    @api.depends('status')
    def _compute_is_active(self):
        for record in self:
            record.is_active = record.status == 'active'

    @api.depends('required_hour_ids.hours_logged', 'extra_hour_ids.hours_logged')
    def _compute_total_hours(self):
        """Compute total hours from all hour records (required + extra)."""
        for record in self:
            record.total_hours = sum(record.required_hour_ids.mapped('hours_logged')) + \
                                sum(record.extra_hour_ids.mapped('hours_logged'))

    @api.depends('required_hour_ids.hours_logged', 'extra_hour_ids.hours_logged', 
                 'training_class_id.class_type_id.hour_requirement_ids')
    def _compute_progression(self):
        for record in self:
            if not record.training_class_id or not record.training_class_id.class_type_id: # type: ignore
                record.progression = 0.0
                continue

            requirements = record.training_class_id.class_type_id.hour_requirement_ids # type: ignore
            if not requirements:
                record.progression = 100.0 if record.total_hours > 0 else 0.0
                continue

            total_required = sum(requirements.mapped('minimum_hours')) # type: ignore
            if total_required <= 0:
                record.progression = 100.0
                continue

            # Calculate actual vs required per activity (Core Syllabus Only - Capped at 100%)
            total_progress = 0.0
            for req in requirements:
                logged = sum(record.required_hour_ids.filtered(
                    lambda h: h.activity_id == req.activity_id
                ).mapped('hours_logged')) # type: ignore
                if req.minimum_hours > 0:
                    # Cap each mandatory activity at its required minimum for the syllabus progression
                    total_progress += min(logged, req.minimum_hours)

            record.progression = (total_progress / total_required) * 100.0

    @api.depends('required_hour_ids.hours_logged', 'required_hour_ids.minimum_hours')
    def _compute_remaining_hours(self):
        """Calculate the sum of hours still required for mandatory activities."""
        for record in self:
            remaining = 0.0
            for req in record.required_hour_ids:
                if req.minimum_hours > req.hours_logged:  # type: ignore
                    remaining += (req.minimum_hours - req.hours_logged)  # type: ignore
            record.remaining_hours = remaining
    @api.depends('required_hour_ids.hours_logged', 'required_hour_ids.minimum_hours', 'required_hour_ids.activity_id')
    def _compute_remaining_breakdown_html(self):
        """Generate a pretty HTML summary of remaining hours per activity."""
        for record in self:
            # Filter for incomplete mandatory items
            incomplete = record.required_hour_ids.filtered(lambda x: x.remaining_hours > 0) # type: ignore
            if not incomplete:
                record.remaining_breakdown_html = '<span class="text-success small"><i class="fa fa-check-circle"/> Syllabus Fully Completed</span>'
                continue
            
            # Sort by most hours remaining (most critical)
            incomplete = sorted(incomplete, key=lambda x: x.remaining_hours, reverse=True) # type: ignore
            
            html = '<div class="d-flex flex-column gap-1">'
            # Show top 3 most critical activities
            for req in incomplete[:3]:
                # Extract values and format as float_time (HH:MM)
                act_name = req.activity_id.name  # type: ignore
                rem_h = req.remaining_hours  # type: ignore
                hours, minutes = divmod(abs(rem_h) * 60, 60)
                rem_h_fmt = f"{int(hours)}:{int(minutes):02d}"
                
                # Determine color based on completion
                progress = req.progress_percentage # type: ignore
                color = "text-danger" if progress < 50 else "text-warning"
                
                html += f'''
                    <div class="d-flex justify-content-between align-items-center small" style="min-width: 220px;">
                        <span class="text-muted text-truncate me-2" style="max-width: 170px;" title="{act_name}">{act_name}</span>
                        <strong class="{color}">{rem_h_fmt} left</strong>
                    </div>
                '''
            
            # Add and more if needed
            if len(incomplete) > 3:
                html += f'<div class="text-muted x-small italic text-center text-decoration-underline mt-1">+{len(incomplete)-3} more activities...</div>'
            
            html += '</div>'
            record.remaining_breakdown_html = html

    @api.constrains('student_id', 'status')
    def _check_one_active_enrollment(self):
        """Ensure student has only one active enrollment."""
        for record in self:
            if record.status == 'active':
                other_active = self.search([
                    ('student_id', '=', record.student_id.id),
                    ('status', '=', 'active'),
                    ('id', '!=', record.id),
                ])
                if other_active:
                    raise ValidationError(
                        f"Student '{record.student_id.name}' already has an active enrollment " # type: ignore
                        f"in class '{other_active[0].training_class_id.name}'." # type: ignore
                    )

    def action_graduate(self):
        """Mark enrollment as graduated. Checks for 100% completion."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.progression < 100.0:
                raise UserError(
                    f"Student '{record.student_id.name}' cannot graduate yet. " # type: ignore
                    f"Syllabus completion is only {record.progression:.1f}%."
                )
            if record.status in ('enrolled', 'active'):
                record.status = 'graduated'
                record.graduation_date = today

    def action_drop(self):
        """Mark enrollment as dropped."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.status in ('enrolled', 'active'):
                record.status = 'dropped'
                record.drop_date = today

    def action_reinstate(self):
        """Reinstate a dropped or graduated student back to appropriate status."""
        for record in self:
            if record.status in ('dropped', 'graduated'):
                # Set status based on class status
                class_status = record.training_class_id.status  # type: ignore
                if class_status == 'in_progress':
                    record.status = 'active'
                elif class_status == 'draft':
                    record.status = 'enrolled'
                else:
                    # For completed/cancelled classes, set to enrolled
                    record.status = 'enrolled'
                # Clear relevant dates
                record.drop_date = False
                record.graduation_date = False
    def action_view_student(self):
        """Open the specific student's form view."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student',
            'res_id': self.student_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    def action_open_enrollment(self):
        """Open the enrollment form in a popup window."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Student Enrollment',
            'res_model': 'fs.student.enrollment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

class FsEnrollmentHours(models.Model):
    """Flight hours logged per activity for an enrollment."""

    _name = 'fs.enrollment.hours'
    _description = 'Enrollment Flight Hours'
    _order = 'activity_id'

    enrollment_id = fields.Many2one(
        comodel_name='fs.student.enrollment',
        string='Enrollment',
        required=True,
        ondelete='cascade',
    )
    is_extra = fields.Boolean(
        string='Extra Hours',
        default=False,
        help="True if these are extra hours added specifically for this student.",
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
        required=True,
        ondelete='restrict',
    )
    discipline_id = fields.Many2one(
        comodel_name='fs.flight.discipline',
        related='activity_id.discipline_id',
        store=True,
    )
    discipline_code = fields.Char(
        string='Discipline Code',
        related='discipline_id.code',
    )
    flight_type_id = fields.Many2one(
        comodel_name='fs.flight.type',
        related='activity_id.flight_type_id',
        store=True,
    )
    flight_type_code = fields.Char(
        string='Type Code',
        related='flight_type_id.code',
    )
    minimum_hours = fields.Float(
        string='Required Hours',
        compute='_compute_minimum_hours',
        store=True,
    )
    hours_logged = fields.Float(
        string='Hours Logged',
        default=0.0,
    )
    progress_percentage = fields.Float(
        string='Progress',
        compute='_compute_progress_percentage',
        store=True,
    )
    remaining_hours = fields.Float(
        string='Remaining',
        compute='_compute_remaining_hours_line',
    )

    @api.depends('hours_logged', 'minimum_hours')
    def _compute_remaining_hours_line(self):
        """Calculate remaining hours for this specific activity."""
        for record in self:
            record.remaining_hours = max(0.0, record.minimum_hours - record.hours_logged)

    @api.depends('hours_logged', 'minimum_hours')
    def _compute_progress_percentage(self):
        """Compute progress percentage for this hour requirement."""
        for record in self:
            if record.minimum_hours > 0:
                record.progress_percentage = (record.hours_logged / record.minimum_hours) * 100.0
            else:
                record.progress_percentage = 100.0 if record.hours_logged > 0 else 0.0

    @api.depends('enrollment_id.training_class_id.class_type_id.hour_requirement_ids',
                 'activity_id')
    def _compute_minimum_hours(self):
        """Get minimum hours from class type requirements."""
        for record in self:
            min_hours = 0.0
            if record.enrollment_id and record.enrollment_id.training_class_id:  # type: ignore
                class_type = record.enrollment_id.training_class_id.class_type_id  # type: ignore
                if class_type:
                    requirement = class_type.hour_requirement_ids.filtered(  # type: ignore
                        lambda r: r.activity_id == record.activity_id
                    )
                    if requirement:
                        min_hours = requirement[0].minimum_hours  # type: ignore
            record.minimum_hours = min_hours

    _unique_activity = models.Constraint(
        'UNIQUE(enrollment_id, activity_id, is_extra)',
        'This activity already exists in this section (Mandatory or Additional).',
    )
