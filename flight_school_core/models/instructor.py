# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class FsInstructor(models.Model):
    """Instructor - Military or civilian instructor."""

    _name = 'fs.instructor'
    _description = 'Instructor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # === Personal Info ===
    name = fields.Char(string='Name', required=True, tracking=True)
    photo = fields.Binary(attachment=True)
    date_of_birth = fields.Date(string='Date of Birth')
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
    email = fields.Char(string='Email', tracking=True)
    mobile = fields.Char(string='Mobile', required=True)
    callsign = fields.Char(
        string='Callsign',
        size=3,
        tracking=True,
        help="Short numeric callsign (max 3 digits)."
    )

    # === Military/Civilian ===
    service_number = fields.Char(string='Service Number')
    rank_id = fields.Many2one('fs.rank', string='Rank')
    rank_name = fields.Char(string='Rank Name', related='rank_id.name', store=True)


    # === Qualifications ===
    license_number = fields.Char(string='License/Rating #')
    license_type = fields.Char(string='License Type')
    license_issue_date = fields.Date(string='License Issue Date')
    license_front_copy = fields.Binary(string='License (Front)', attachment=True)
    license_front_filename = fields.Char(string='License Front Filename')
    license_back_copy = fields.Binary(string='License (Back)', attachment=True)
    license_back_filename = fields.Char(string='License Back Filename')
    
    # Mimetype helpers for conditional view display
    license_front_mimetype = fields.Char(compute='_compute_mimetypes')
    license_back_mimetype = fields.Char(compute='_compute_mimetypes')
    medical_mimetype = fields.Char(compute='_compute_mimetypes')

    qualification_ids = fields.Many2many(
        comodel_name='fs.instructor.qualification',
        string='Instructor Qualifications',
        compute='_compute_qualification_ids',
        readonly=True
    )
    qualification_assignment_ids = fields.One2many(
        comodel_name='fs.instructor.qualification.assignment',
        inverse_name='instructor_id',
        string='Qualification Assignments'
    )
    max_students = fields.Integer(
        string='Max Students',
        default=lambda self: self._get_default_max_students()
    )

    # === Medical ===
    medical_class = fields.Selection(
        selection=[
            ('class_1', 'Class 1'),
            ('class_2', 'Class 2'),
            ('military', 'Military'),
        ],
        string='Medical Class'
    )
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

    # === Assignments ===
    student_ids = fields.One2many(
        comodel_name='fs.student',
        inverse_name='default_instructor_id',
        string='Assigned Students'
    )
    student_count = fields.Integer(
        string='Students',
        compute='_compute_assignment_stats',
        store=True,
        help="Number of active students assigned to this instructor."
    )
    is_overloaded = fields.Boolean(
        string='Overloaded',
        compute='_compute_assignment_stats',
        store=True,
        help="True when student load exceeds configured maximum."
    )

    # === Availability & Workload ===
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('on_leave', 'On Leave'),
            ('deployed', 'Deployed'),
            ('medical_hold', 'Medical Hold'),
            ('retired', 'Retired'),
        ],
        string='Status',
        default='available',
        tracking=True
    )
    total_hours = fields.Float(string='Total Hours', default=0.0)
    hours_this_month = fields.Float(string='Hours This Month', default=0.0)
    hours_this_3months = fields.Float(string='Hours This 3 Months', default=0.0)
    max_hours_per_month = fields.Float(
        string='Max Hours / Month',
        default=lambda self: self._get_default_max_hours_per_month()
    )
    max_hours_per_3months = fields.Float(
        string='Max Hours / 3 Months',
        default=lambda self: self._get_default_max_hours_per_3months()
    )

    # === Contact ===
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')

    active = fields.Boolean(string='Active', default=True, tracking=True)

    _email_unique = models.Constraint(
        'UNIQUE(email)',
        'Email must be unique.'
    )

    # === Default Helpers ===
    @api.model
    def _get_config_int(self, key, default_value):
        try:
            # get_param is a method of ir.config_parameter, but the linter sees BaseModel
            value = self.env['ir.config_parameter'].sudo().get_param(key, default_value)  # type: ignore
            return int(value)
        except (TypeError, ValueError):
            return default_value

    @api.model
    def _get_config_float(self, key, default_value):
        try:
            # get_param is a method of ir.config_parameter, but the linter sees BaseModel
            value = self.env['ir.config_parameter'].sudo().get_param(key, default_value)  # type: ignore
            return float(value)
        except (TypeError, ValueError):
            return default_value

    @api.model
    def _get_default_max_students(self):
        return self._get_config_int('flight_school.default_max_students', 8)

    @api.model
    def _get_default_max_hours_per_month(self):
        return self._get_config_float('flight_school.default_max_hours_per_month', 80.0)

    @api.model
    def _get_default_max_hours_per_3months(self):
        return self._get_config_float('flight_school.default_max_hours_per_3months', 240.0)

    @api.model
    def _get_medical_warning_days(self):
        return self._get_config_int('flight_school.medical_warning_days', 30)

    # === Display Name ===
    @api.depends('callsign', 'name')
    def _compute_display_name(self):
        for record in self:
            names = []
            if record.callsign:
                names.append(f"[{record.callsign}]")
            if record.name:
                names.append(record.name)
            record.display_name = " ".join(names)

    # === Computes ===
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

    @api.depends('license_front_filename', 'license_back_filename', 'medical_certificate_filename')
    def _compute_mimetypes(self):
        for record in self:
            def get_mimetype(filename):
                if not filename: return False
                ext = filename.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']: return 'image'
                if ext == 'pdf': return 'pdf'
                return 'other'
            record.license_front_mimetype = get_mimetype(record.license_front_filename)
            record.license_back_mimetype = get_mimetype(record.license_back_filename)
            record.medical_mimetype = get_mimetype(record.medical_certificate_filename)

    @api.depends('qualification_assignment_ids.qualification_id')
    def _compute_qualification_ids(self):
        """Mirror assigned qualifications so tag widgets stay in sync."""
        for record in self:
            record.qualification_ids = record.mapped('qualification_assignment_ids.qualification_id')

    @api.depends('student_ids', 'student_ids.enrollment_status', 'max_students')
    def _compute_assignment_stats(self):
        for record in self:
            active_students = record.student_ids.filtered_domain([('enrollment_status', '=', 'active')])
            record.student_count = len(active_students)
            record.is_overloaded = bool(record.max_students and record.student_count > record.max_students)

    # === Onchange ===
    @api.onchange('student_count', 'max_students')
    def _onchange_overload(self):
        if self.max_students and self.student_count > self.max_students:
            return {
                'warning': {
                    'title': _('Instructor Overloaded'),
                    'message': _('This instructor has more students than the configured maximum.'),
                }
            }
        return {}

    @api.onchange('service_number')
    def _onchange_service_number(self):
        if self.service_number:
            self.service_number = self.service_number.upper()

    @api.onchange('mobile')
    def _onchange_mobile(self):
        if self.mobile:
            self.mobile = self._format_mobile_number(self.mobile)

    @api.onchange('medical_expiry_date')
    def _onchange_medical_expiry(self):
        warnings = []
        today = fields.Date.context_today(self)
        warning_days = self._get_medical_warning_days()
        if self.medical_expiry_date and self.medical_expiry_date <= today + relativedelta(days=warning_days):
            warnings.append(_('Medical certificate expires within %s days.') % warning_days)
        if warnings:
            return {
                'warning': {
                    'title': _('Expiry Warning'),
                    'message': " ".join(warnings),
                }
            }
        return {}

    # === CRUD Overrides ===
    def unlink(self):
        """Archive instead of deleting when linked to students."""
        to_delete = self.filtered(lambda rec: not rec.student_ids)
        to_archive = self - to_delete
        if to_archive:
            to_archive.write({'active': False})
        if to_delete:
            return super(FsInstructor, to_delete).unlink()
        return True

    @api.constrains('callsign')
    def _check_callsign_format(self):
        for record in self:
            if record.callsign and (len(record.callsign) > 3 or not record.callsign.isdigit()):
                raise ValidationError(_("Callsign must be up to 3 numeric characters."))

    # === CRUD Overrides ===
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('callsign'):
                vals['callsign'] = vals['callsign'].upper()
            if vals.get('service_number'):
                vals['service_number'] = vals['service_number'].upper()
            if vals.get('mobile'):
                vals['mobile'] = self._format_mobile_number(vals['mobile'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('callsign'):
            vals['callsign'] = vals['callsign'].upper()
        if vals.get('service_number'):
            vals['service_number'] = vals['service_number'].upper()
        if vals.get('mobile'):
            vals['mobile'] = self._format_mobile_number(vals['mobile'])
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
