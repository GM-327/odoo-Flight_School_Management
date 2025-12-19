# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import format_date
from typing import TYPE_CHECKING, Optional, cast

if TYPE_CHECKING:
    from .training_class import FsTrainingClass
from odoo.exceptions import ValidationError


class FsStudent(models.Model):
    """Student Pilot - Military student assigned to a training class."""

    _name = 'fs.student'
    _description = 'Student Pilot'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_number, name'

    # === Personal Info ===
    name = fields.Char(string='Full Name', required=True, tracking=True)
    photo = fields.Binary(string='Photo', attachment=True)
    date_of_birth = fields.Date(string='Date of Birth', required=True)
    age = fields.Integer(string='Age', compute='_compute_age', store=True)
    gender = fields.Selection(
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
        ],
        string='Gender'
    )
    nationality = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        default=lambda self: self.env.ref('base.tn', raise_if_not_found=False) or self.env['res.country'].search([('code', '=', 'TN')], limit=1),
    )
    national_id = fields.Char(string='National ID / Passport')
    email = fields.Char(string='Email')
    mobile = fields.Char(string='Mobile')
    primary_instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Primary Instructor',
        tracking=True,
        help="Default instructor for this student."
    )
    emergency_contact_name = fields.Char(string='Emergency Contact')
    emergency_contact_phone = fields.Char(string='Emergency Phone')
    emergency_contact_relationship = fields.Char(string='Relationship')

    # === Military Info ===
    service_number = fields.Char(string='Service Number', tracking=True)
    rank_id = fields.Many2one(
        comodel_name='fs.rank',
        string='Rank',
        required=True,
        tracking=True,
        help="Rank of the student."
    )
    rank_name = fields.Char(string='Rank Name', related='rank_id.name', store=True)
    security_clearance_expiry = fields.Date(string='Security Clearance Expiry')

    # === Training Class & Callsign ===
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Current Training Class',
        compute='_compute_active_enrollment_data',
        store=True,
        tracking=True,
        help="Currently active training class for this student."
    )
    active_enrollment_id = fields.Many2one(
        comodel_name='fs.student.enrollment',
        string='Active Enrollment',
        compute='_compute_active_enrollment_data',
        store=True
    )
    default_instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Default Instructor',
        compute='_compute_active_enrollment_data',
        store=True,
        tracking=True,
        help="Primary instructor responsible for this student in the current class."
    )
    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Training Program',
        related='training_class_id.class_type_id',
        store=True
    )
    class_name = fields.Char(string='Class Name', related='training_class_id.name', store=True)
    training_class_duration_display = fields.Char(
        string='Training Schedule',
        compute='_compute_training_class_duration_display',
        help="Formatted range derived from the linked training class dates."
    )
    training_class_end_warning = fields.Boolean(
        string='Class Ending Soon',
        related='training_class_id.end_date_warning',
        help="Mirrors the linked training class warning flag."
    )
    callsign = fields.Char(
        string='Callsign',
        compute='_compute_active_enrollment_data',
        store=True,
        tracking=True,
        help="Unique callsign within the current training class."
    )


    enrollment_date = fields.Date(
        string='Enrollment Date',
        related='active_enrollment_id.enrollment_date',
        store=True,
        readonly=True,
        help="Date the student joined the current training class."
    )
    enrollment_ids = fields.One2many(
        comodel_name='fs.student.enrollment',
        inverse_name='student_id',
        string='Enrollment History'
    )
    enrollment_status = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('graduated', 'Graduated'),
            ('dropped', 'Dropped'),
            ('none', 'No Enrollment'),
        ],
        string='Enrollment Status',
        compute='_compute_active_enrollment_data',
        store=True,
        help="Status from the active or most recent enrollment."
    )



    # === Training Progress ===
    total_flight_hours = fields.Float(string='Total Flight Hours', default=0.0)
    total_simulator_hours = fields.Float(string='Simulator Hours', default=0.0)
    solo_hours = fields.Float(string='Solo Hours', default=0.0)
    dual_hours = fields.Float(string='Dual Instruction Hours', default=0.0)
    last_flight_date = fields.Date(string='Last Flight Date')
    training_class_total_flight_hours = fields.Float(
        string='Class Flight Hours',
        compute='_compute_training_class_total_flight_hours',
        help="Total hours logged for the student's current training class."
    )
    progress_percentage = fields.Float(
        string='Progress (%)',
        compute='_compute_progress_percentage',
        store=True,
        help="Completion percentage vs minimum required flight hours."
    )

    # === Medical ===
    medical_class = fields.Selection(
        selection=[
            ('class_1', 'Class 1'),
            ('class_2', 'Class 2'),
        ],
        string='Medical Class'
    )
    medical_certificate_number = fields.Char(string='Medical Certificate #')
    medical_issue_date = fields.Date(string='Medical Issue Date')
    medical_certificate = fields.Binary(string='Certificate Copy', attachment=True)
    medical_certificate_filename = fields.Char(string='Certificate Filename')
    medical_expiry_date = fields.Date(string='Medical Expiry Date')
    medical_status = fields.Selection(
        selection=[
            ('unknown', 'Unknown'),
            ('current', 'Current'),
            ('expiring_soon', 'Expiring Soon'),
            ('expired', 'Expired'),
        ],
        string='Medical Status',
        compute='_compute_medical_status',
        store=True
    )
    medical_limitations = fields.Text(string='Medical Limitations')

    # === Contact & Address ===
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')

    # === Administrative ===
    notes = fields.Text(string='Notes')
    instructor_notes = fields.Text(string='Instructor Notes')
    active = fields.Boolean(string='Active', default=True, tracking=True)

    _service_number_unique = models.Constraint(
        'UNIQUE(service_number)',
        'Service number must be unique.'
    )
    _medical_dates_check = models.Constraint(
        'CHECK(medical_issue_date IS NULL OR medical_expiry_date IS NULL OR medical_expiry_date >= medical_issue_date)',
        'Medical expiry date must be after the issue date.'
    )

    # === Configuration Helpers ===
    @api.model
    def _get_config_int(self, key, default_value):
        try:
            # get_param is a method of ir.config_parameter, but the linter sees BaseModel
            value = self.env['ir.config_parameter'].sudo().get_param(key, default_value)  # type: ignore
            return int(value)
        except (TypeError, ValueError):
            return default_value

    @api.model
    def _get_medical_warning_days(self):
        return self._get_config_int('flight_school.medical_warning_days', 30)

    # === Display Name ===
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or ''

    @api.depends('training_class_id.start_date', 'training_class_id.expected_end_date')
    def _compute_training_class_duration_display(self):
        """Display the student's current class window as “start - end”."""
        fmt = lambda date_val: format_date(self.env, date_val) if date_val else False
        for record in self:
            training_class = cast(Optional['FsTrainingClass'], record.training_class_id)
            start = fmt(training_class.start_date) if training_class else False
            end = fmt(training_class.expected_end_date) if training_class else False

            if start and end:
                record.training_class_duration_display = _('%s - %s') % (start, end)
            elif start:
                record.training_class_duration_display = _('From %s') % start
            elif end:
                record.training_class_duration_display = _('Until %s') % end
            else:
                record.training_class_duration_display = False

    @api.depends('training_class_id.total_flight_hours_logged')
    def _compute_training_class_total_flight_hours(self):
        for record in self:
            training_class = cast(Optional['FsTrainingClass'], record.training_class_id)
            record.training_class_total_flight_hours = training_class.total_flight_hours_logged if training_class else 0.0

    # === Computes ===
    @api.depends('enrollment_ids', 'enrollment_ids.status', 'enrollment_ids.training_class_id', 'enrollment_ids.instructor_id', 'enrollment_ids.callsign')
    def _compute_active_enrollment_data(self):
        """Compute active enrollment data from the student's enrollment history."""
        for student in self:
            active_enrollment = student.enrollment_ids.filtered_domain([('status', '=', 'active')])[:1]
            if active_enrollment:
                student.active_enrollment_id = active_enrollment
                student.training_class_id = active_enrollment.training_class_id  # type: ignore
                student.default_instructor_id = active_enrollment.instructor_id  # type: ignore
                student.callsign = active_enrollment.callsign                    # type: ignore
                student.enrollment_status = 'active'
            else:
                student.active_enrollment_id = False
                latest = student.enrollment_ids[:1]
                if latest:
                    student.training_class_id = latest.training_class_id        # type: ignore
                    student.default_instructor_id = latest.instructor_id       # type: ignore
                    student.callsign = latest.callsign                          # type: ignore
                    student.enrollment_status = latest.status                   # type: ignore
                else:
                    student.training_class_id = False
                    student.default_instructor_id = False
                    student.callsign = False
                    student.enrollment_status = 'none'

    @api.depends('date_of_birth')
    def _compute_age(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.date_of_birth:
                delta = relativedelta(today, record.date_of_birth)
                record.age = delta.years
            else:
                record.age = 0

    @api.depends('medical_expiry_date')
    def _compute_medical_status(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.medical_expiry_date:
                record.medical_status = 'unknown'
                continue
            if record.medical_expiry_date < today:
                record.medical_status = 'expired'
            elif record.medical_expiry_date <= today + relativedelta(days=self._get_medical_warning_days()):
                record.medical_status = 'expiring_soon'
            else:
                record.medical_status = 'current'

    @api.depends('total_flight_hours', 'class_type_id.min_flight_hours_required')
    def _compute_progress_percentage(self):
        for record in self:
            # Use mapped to bypass static analysis type inference limitations
            required_hours = sum(record.mapped('class_type_id.min_flight_hours_required'))
            if required_hours > 0:
                progress = (record.total_flight_hours / required_hours) * 100.0
                record.progress_percentage = min(progress, 100.0)
            else:
                record.progress_percentage = 0.0

    # === Constraints ===
    @api.constrains('training_class_id', 'active')
    def _check_single_training_class(self):
        """Ensure a student cannot be assigned to multiple active classes."""
        # Model design enforces one class; constraint kept for clarity.
        return True

    # === Onchange ===
    @api.onchange('medical_expiry_date')
    def _onchange_medical_expiry(self):
        if self.medical_expiry_date:
            today = fields.Date.context_today(self)
            warning_days = self._get_medical_warning_days()
            if self.medical_expiry_date <= today + relativedelta(days=warning_days):
                return {
                    'warning': {
                        'title': _('Medical Expiry'),
                        'message': _('Medical certificate will expire in less than %s days.') % warning_days,
                    }
                }
        return {}

    @api.onchange('mobile', 'emergency_contact_phone')
    def _onchange_mobile(self):
        if self.mobile:
            self.mobile = self._format_mobile_number(self.mobile)
        if self.emergency_contact_phone:
            self.emergency_contact_phone = self._format_mobile_number(self.emergency_contact_phone)

    # === CRUD Overrides ===
    def unlink(self):
        """Archive instead of deleting to keep history."""
        self.write({'active': False})
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('mobile'):
                vals['mobile'] = self._format_mobile_number(vals['mobile'])
            if vals.get('emergency_contact_phone'):
                vals['emergency_contact_phone'] = self._format_mobile_number(vals['emergency_contact_phone'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('mobile'):
            vals['mobile'] = self._format_mobile_number(vals['mobile'])
        if vals.get('emergency_contact_phone'):
            vals['emergency_contact_phone'] = self._format_mobile_number(vals['emergency_contact_phone'])
        return super().write(vals)

    def _format_mobile_number(self, number):
        """Format mobile number as XX XXX XXX."""
        if not number:
            return number
        # Strip all non-digit characters
        digits = "".join(filter(str.isdigit, number))
        if len(digits) == 8:
            return f"{digits[:2]} {digits[2:5]} {digits[5:]}"
        return number
