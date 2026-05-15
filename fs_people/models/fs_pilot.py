# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People fs pilot module.

Purpose:
    Defines classes FsPilot for students, instructors, pilots, administrative staff, qualifications, licenses, and medical tracking.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training enrolls people in classes.
"""
from datetime import timedelta
from odoo import api, fields, models


class FsPilot(models.Model):
    """Licensed pilot using the flight school fleet.

    Pilots are licensed aviators who use the school's aircraft
    but are not students or instructors.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.pilot``.
        _inherit: Odoo model(s) extended by this class: ``['fs.person']``.
        _description (str): Human-readable model label, ``Pilot``.

    Related:
        fs_training enrolls people in classes.
        fs_scheduling exposes people through the crew-member SQL view.
    """

    _name = 'fs.pilot'
    _description = 'Pilot'
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
        help="Callsign for the pilot.",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
    )

    @api.depends('name', 'callsign')
    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        show_name = self.env.context.get('show_name_only', False)
        for record in self:
            if show_name:
                # type: ignore[attr-defined]
                record.display_name = record.name or ''
            elif record.callsign:
                record.display_name = record.callsign  # type: ignore
            else:
                # type: ignore[attr-defined]
                record.display_name = record.name or ''

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
        string='Qualification Badges',
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
        """Compute HTML badges for qualifications with status-based colors.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        status_colors = {
            'valid': '#28a745',      # Green
            'expiring': '#ffc107',   # Yellow
            'expired': '#dc3545',    # Red
            'no_expiry': '#6c757d',  # Gray
        }
        for record in self:
            badges = []
            for qual in record.qualification_ids:
                color = status_colors.get(
                    qual.expiry_status, '#6c757d')  # type: ignore
                text_color = '#212529' if qual.expiry_status == 'expiring' else '#ffffff'  # type: ignore
                badge_html = (
                    f'<span style="background-color: {color}; color: {text_color}; '
                    f'padding: 2px 8px; border-radius: 4px; margin-right: 4px; '
                    f'font-size: 12px; display: inline-block;">'
                    # type: ignore
                    f'{qual.qualification_code or qual.qualification_id.name}</span>'
                )
                badges.append(badge_html)
            record.qualification_badges = ''.join(badges) if badges else ''

    def action_view_qualifications(self):
        """Navigate to the detailed qualifications list in a popup.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'name': 'Qualifications & Ratings',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.person.qualification',
            'view_mode': 'list',
            'domain': [('id', 'in', self.qualification_ids.ids)],
            'context': {'default_pilot_id': self.id},
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
        help="The most urgent expiry date among medical, english, security, insurance, and qualifications.",
    )

    @api.depends('qualification_ids.expiry_status', 'qualification_ids.expiry_date', 'medical_status',
                 'english_status', 'security_clearance_status', 'insurance_status')
    def _compute_has_expired_qualification(self):
        """Check if any qualification or status is expired and find earliest expiry.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.has_expired_qualification = (
                # type: ignore
                any(qual.expiry_status == 'expired' for qual in record.qualification_ids) or
                getattr(record, 'medical_status', False) == 'expired' or
                record.english_status == 'expired' or  # type: ignore
                record.security_clearance_status == 'expired' or  # type: ignore
                record.insurance_status == 'expired'  # type: ignore
            )

            # Find earliest expiry date
            expiries = []
            med_exp = getattr(record, 'medical_expiry', False)
            if med_exp:
                expiries.append(med_exp)

            eng_exp = getattr(record, 'english_expiry', False)
            if eng_exp:
                expiries.append(eng_exp)

            sec_exp = getattr(record, 'security_clearance_expiry', False)
            if sec_exp:
                expiries.append(sec_exp)

            ins_exp = getattr(record, 'insurance_expiry', False)
            if ins_exp:
                expiries.append(ins_exp)

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
        """Compute English proficiency status based on expiry date and warning period from settings.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
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
        """Compute security clearance status based on expiry date.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.security_warning_days', '30'))
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
        """Compute insurance status based on expiry date.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
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
    total_sim_hours = fields.Float(
        string='Total Sim Hours',
        help="Total logged simulator hours.",
    )
    solo_hours = fields.Float(
        string='Solo Hours',
        help="Total solo flight hours.",
    )
    last_flight_date = fields.Date(
        string='Last Flight Date',
        help="Date of the most recent flight.",
    )
