# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta
from odoo import api, fields, models


class FsInstructor(models.Model):
    """Flight instructor in the flight school system."""
    
    _name = 'fs.instructor'
    _description = 'Flight Instructor'
    _inherit = ['fs.person']
    _order = 'name'

    department_id = fields.Many2one(
        'fs.department',
        string='Department',
        tracking=True,
    )

    # === Callsign ===
    callsign = fields.Char(
        string='Callsign',
        help="Callsign for the instructor.",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
    )

    @api.depends('name', 'callsign')
    def _compute_display_name(self):
        for record in self:
            if record.callsign:
                record.display_name = f"[{record.callsign}] {record.name}"  # type: ignore
            else:
                record.display_name = record.name or ''  # type: ignore

    # === License & Qualifications ===
    license_id = fields.Many2one(
        comodel_name='fs.license.type',
        string='License Type',
        domain=[('is_student_related', '=', False)],
        help="Instructor license type.",
    )
    license_code = fields.Char(
        string='License',
        related='license_id.code',
    )
    license_number = fields.Char(
        string='License #',
    )
    license_issue_date = fields.Date(
        string='License Issue Date',
    )
    qualification_ids = fields.One2many(
        comodel_name='fs.person.qualification',
        inverse_name='instructor_id',
        string='Qualifications',
    )
    qualification_badges = fields.Html(
        string='Qualification Badges',
        compute='_compute_qualification_badges',
        sanitize=False,
    )
    
    @api.depends('qualification_ids', 'qualification_ids.qualification_code', 'qualification_ids.expiry_status')
    def _compute_qualification_badges(self):
        """Compute HTML badges for qualifications with status-based colors."""
        status_colors = {
            'valid': '#28a745',      # Green
            'expiring': '#ffc107',   # Yellow
            'expired': '#dc3545',    # Red
            'no_expiry': '#6c757d',  # Gray
        }
        for record in self:
            badges = []
            for qual in record.qualification_ids:
                color = status_colors.get(qual.expiry_status, '#6c757d')  # type: ignore
                text_color = '#212529' if qual.expiry_status == 'expiring' else '#ffffff'  # type: ignore
                badge_html = (
                    f'<span style="background-color: {color}; color: {text_color}; '
                    f'padding: 2px 8px; border-radius: 4px; margin-right: 4px; '
                    f'font-size: 12px; display: inline-block;">'
                    f'{qual.qualification_code or qual.qualification_id.name}</span>'  # type: ignore
                )
                badges.append(badge_html)
            record.qualification_badges = ''.join(badges) if badges else ''

    def action_view_qualifications(self):
        """Navigate to the detailed qualifications list in a popup."""
        self.ensure_one()
        return {
            'name': 'Qualifications & Ratings',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.person.qualification',
            'view_mode': 'list',
            'domain': [('id', 'in', self.qualification_ids.ids)],
            'context': {'default_instructor_id': self.id},
            'target': 'new',
        }

    has_expired_qualification = fields.Boolean(
        string='Has Expired Qualification',
        compute='_compute_has_expired_qualification',
        store=True,
    )
    earliest_expiry_date = fields.Date(
        string='Earliest Expiry',
        compute='_compute_has_expired_qualification',
        store=True,
        help="The most urgent expiry date among medical, english, and qualifications.",
    )
    
    @api.depends('qualification_ids.expiry_status', 'qualification_ids.expiry_date', 
                 'medical_expiry', 'english_expiry')
    def _compute_has_expired_qualification(self):
        """Check if any qualification or status is expired and find the earliest expiry date."""
        for record in self:
            # Check for expiration
            record.has_expired_qualification = (
                any(qual.expiry_status == 'expired' for qual in record.qualification_ids) or  # type: ignore
                getattr(record, 'medical_status', False) == 'expired' or
                getattr(record, 'english_status', False) == 'expired'
            )
            
            # Find earliest expiry date
            expiries = []
            med_exp = getattr(record, 'medical_expiry', False)
            if med_exp:
                expiries.append(med_exp)
            
            eng_exp = getattr(record, 'english_expiry', False)
            if eng_exp:
                expiries.append(eng_exp)
                
            for qual in record.qualification_ids:
                q_exp = getattr(qual, 'expiry_date', False)
                if q_exp:
                    expiries.append(q_exp)
            
            record.earliest_expiry_date = min(expiries) if expiries else False

    # === English Proficiency ===
    english_level_id = fields.Many2one(
        comodel_name='fs.english.level',
        string='English Level',
    )
    english_expiry = fields.Date(
        string='English Expiry',
    )
    english_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='English Status',
        compute='_compute_english_status',
        store=True,
    )
    
    @api.depends('english_expiry')
    def _compute_english_status(self):
        """Compute English proficiency status based on expiry date and warning period from settings."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.english_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)
        
        for record in self:
            if not record.english_expiry:
                record.english_status = 'no_expiry'
            elif record.english_expiry < today:
                record.english_status = 'expired'
            elif record.english_expiry <= warning_date:
                record.english_status = 'expiring'
            else:
                record.english_status = 'valid'
    
    # === Capacity Limits ===
    max_students = fields.Integer(
        string='Max Students',
        default=lambda self: int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.default_max_students', '8')),
        help="Maximum number of students this instructor can have.",
        readonly=True,
    )
    max_hours_per_month = fields.Float(
        string='Max Hours/Month',
        default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.default_max_hours_per_month', '80.0')),
        help="Maximum instruction hours per month.",
        readonly=True,
    )
    max_hours_per_3months = fields.Float(
        string='Max Hours/3 Months',
        default=lambda self: float(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.default_max_hours_per_3months', '240.0')),
        help="Maximum instruction hours per rolling 3-month period.",
        readonly=True,
    )
    
    # === Experience ===
    total_flight_hours = fields.Float(
        string='Total Flight Hours',
        help="Total logged flight hours.",
    )
    total_instruction_hours = fields.Float(
        string='Total Instruction Hours',
        help="Total logged instruction hours.",
    )
    
    hours_current_month = fields.Float(
        string='Hours (Current Month)',
        compute='_compute_rolling_hours',
        help="Instruction hours logged in the current calendar month.",
    )
    hours_3months = fields.Float(
        string='Hours (Rolling 3 Months)',
        compute='_compute_rolling_hours',
        help="Instruction hours logged in the current and previous two months.",
    )
    
    hours_current_month_status = fields.Selection(
        selection=[('ok', 'OK'), ('warning', 'Near Limit'), ('danger', 'Over Limit')],
        compute='_compute_rolling_hours_status',
    )
    hours_3months_status = fields.Selection(
        selection=[('ok', 'OK'), ('warning', 'Near Limit'), ('danger', 'Over Limit')],
        compute='_compute_rolling_hours_status',
    )

    def _compute_rolling_hours(self):
        """Compute monthly and 3-month rolling hours.
        Note: Currently returns 0.0 as the individual flight log model is not yet integrated.
        """
        for record in self:
            # Placeholder for future integration with fs.flight.log
            record.hours_current_month = 0.0
            record.hours_3months = 0.0

    @api.depends('hours_current_month', 'max_hours_per_month', 'hours_3months', 'max_hours_per_3months')
    def _compute_rolling_hours_status(self):
        """Compute status based on percentage of max hours."""
        for record in self:
            # Current Month Status
            if record.max_hours_per_month > 0:
                ratio = record.hours_current_month / record.max_hours_per_month
                if ratio >= 1.0:
                    record.hours_current_month_status = 'danger'
                elif ratio >= 0.8:
                    record.hours_current_month_status = 'warning'
                else:
                    record.hours_current_month_status = 'ok'
            else:
                record.hours_current_month_status = 'ok'
                
            # 3-Month Status
            if record.max_hours_per_3months > 0:
                ratio = record.hours_3months / record.max_hours_per_3months
                if ratio >= 1.0:
                    record.hours_3months_status = 'danger'
                elif ratio >= 0.8:
                    record.hours_3months_status = 'warning'
                else:
                    record.hours_3months_status = 'ok'
            else:
                record.hours_3months_status = 'ok'

    # === Assigned Students ===
    # These fields are and logic are handled in the fs_training module
    # via model inheritance to avoid circular dependencies and errors
    # when the Training module is not installed.

