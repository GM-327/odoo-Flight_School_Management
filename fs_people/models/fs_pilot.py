# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta
from odoo import api, fields, models


class FsPilot(models.Model):
    """Licensed pilot using the flight school fleet.
    
    Pilots are licensed aviators who use the school's aircraft
    but are not students or instructors.
    """
    
    _name = 'fs.pilot'
    _description = 'Pilot'
    _inherit = ['fs.person']
    _order = 'name'

    # === Callsign ===
    callsign = fields.Char(
        string='Callsign',
        help="Callsign for the pilot.",
    )

    # === License & Qualifications ===
    license_id = fields.Many2one(
        comodel_name='fs.license.type',
        string='License',
        domain=[('is_student_related', '=', False)],
        help="Pilot license type.",
    )
    license_code = fields.Char(
        string='License Code',
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
        inverse_name='pilot_id',
        string='Qualifications',
    )
    qualification_badges = fields.Html(
        string='Qualifications',
        compute='_compute_qualification_badges',
        sanitize=False,
    )
    has_expired_qualification = fields.Boolean(
        string='Has Expired Qualification',
        compute='_compute_has_expired_qualification',
        store=True,
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
    
    @api.depends('qualification_ids.expiry_status')
    def _compute_has_expired_qualification(self):
        """Check if any qualification is expired for row decoration."""
        for record in self:
            record.has_expired_qualification = any(
                qual.expiry_status == 'expired'  # type: ignore
                for qual in record.qualification_ids
            )

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
    
    # === Civilian Specific (when is_military = False) ===
    security_clearance_expiry = fields.Date(
        string='Security Clearance Expiry',
        help="For civilian pilots: security clearance expiry date.",
    )
    security_clearance_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='Security Status',
        compute='_compute_security_clearance_status',
        store=True,
    )
    insurance_expiry = fields.Date(
        string='Insurance Expiry',
        help="For civilian pilots: liability insurance expiry date.",
    )
    insurance_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='Insurance Status',
        compute='_compute_insurance_status',
        store=True,
    )
    
    @api.depends('security_clearance_expiry')
    def _compute_security_clearance_status(self):
        """Compute security clearance status based on expiry date."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.insurance_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)
        
        for record in self:
            if not record.security_clearance_expiry:
                record.security_clearance_status = 'no_expiry'
            elif record.security_clearance_expiry < today:
                record.security_clearance_status = 'expired'
            elif record.security_clearance_expiry <= warning_date:
                record.security_clearance_status = 'expiring'
            else:
                record.security_clearance_status = 'valid'
    
    @api.depends('insurance_expiry')
    def _compute_insurance_status(self):
        """Compute insurance status based on expiry date."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.insurance_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)
        
        for record in self:
            if not record.insurance_expiry:
                record.insurance_status = 'no_expiry'
            elif record.insurance_expiry < today:
                record.insurance_status = 'expired'
            elif record.insurance_expiry <= warning_date:
                record.insurance_status = 'expiring'
            else:
                record.insurance_status = 'valid'
    
    
    # === Financial ===
    advance_payment = fields.Monetary(
        string='Advance Payment',
        currency_field='currency_id',
        help="Prepaid balance for flight hours.",
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,  # type: ignore
    )
    
    # === Experience ===
    total_flight_hours = fields.Float(
        string='Total Flight Hours',
        help="Total logged flight hours.",
    )
