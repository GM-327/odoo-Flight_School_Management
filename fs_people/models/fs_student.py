# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta
from odoo import api, fields, models


class FsStudent(models.Model):
    """Flight student in the flight school system.
    
    Note: Enrollment in training classes is handled by fs_training module.
    A student can be enrolled in multiple classes but active in only one.
    """
    
    _name = 'fs.student'
    _description = 'Flight Student'
    _inherit = ['fs.person']
    _order = 'name'
    license_id = fields.Many2one(
        comodel_name='fs.license.type',
        string='License',
        domain=[('is_student_related', '=', True)],
        help="Student license type (e.g., Student Card).",
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
    license_expiry = fields.Date(
        string='License Expiry',
        help="Only applicable for Student Card.",
    )
    license_expiry_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='License Status',
        compute='_compute_license_expiry_status',
        store=True,
    )
    
    @api.depends('license_expiry')
    def _compute_license_expiry_status(self):
        """Compute license expiry status based on expiry date."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.license_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)
        
        for record in self:
            if not record.license_expiry:
                record.license_expiry_status = 'no_expiry'
            elif record.license_expiry < today:
                record.license_expiry_status = 'expired'
            elif record.license_expiry <= warning_date:
                record.license_expiry_status = 'expiring'
            else:
                record.license_expiry_status = 'valid'
    
    has_expired_status = fields.Boolean(
        string='Has Expired Status',
        compute='_compute_has_expired_status',
        store=True,
    )
    
    @api.depends('license_expiry_status', 'medical_status', 'security_clearance_status', 'insurance_status')
    def _compute_has_expired_status(self):
        """Check if any status is expired for row decoration."""
        for record in self:
            record.has_expired_status = (
                record.license_expiry_status == 'expired' or  # type: ignore
                record.medical_status == 'expired' or  # type: ignore
                record.security_clearance_status == 'expired' or  # type: ignore
                record.insurance_status == 'expired'  # type: ignore
            )

    # === Civilian Specific (when is_military = False) ===
    security_clearance_expiry = fields.Date(
        string='Security Clearance Expiry',
        help="For civilian students: security clearance expiry date.",
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
        help="For civilian students: liability insurance expiry date.",
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
    advance_payment = fields.Monetary(
        string='Advance Payment',
        currency_field='currency_id',
        help="Prepaid balance for flight hours (Civilian students only).",
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
    solo_hours = fields.Float(
        string='Solo Hours',
        help="Total solo flight hours.",
    )
    



