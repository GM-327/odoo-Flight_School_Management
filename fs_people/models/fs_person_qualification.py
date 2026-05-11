# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from calendar import monthrange
from datetime import date, timedelta

from odoo import api, fields, models


class FsPersonQualification(models.Model):
    """Person's qualification with issue/expiry tracking.

    This model links a person (instructor/pilot) to their qualifications
    with individual issue and expiry dates.
    """

    _name = 'fs.person.qualification'
    _description = 'Person Qualification'
    _order = 'expiry_date'
    _rec_name = 'qualification_id'

    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
        ondelete='cascade',
    )
    pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Pilot',
        ondelete='cascade',
    )
    qualification_id = fields.Many2one(
        comodel_name='fs.qualification.type',
        string='Qualification',
        required=True,
        ondelete='restrict',
    )
    qualification_code = fields.Char(
        string='Code',
        related='qualification_id.code',
    )
    qualification_name = fields.Char(
        string='Name',
        related='qualification_id.name',
    )
    issue_date = fields.Date(
        string='Issue Date',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )
    validity_months = fields.Integer(
        string='Validity (Months)',
        related='qualification_id.validity_months',
    )
    expiry_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='Status',
        compute='_compute_expiry_status',
        store=True,
    )
    notes = fields.Text(
        string='Notes',
    )

    @api.depends('expiry_date')
    def _compute_expiry_status(self):
        """Compute expiry status based on expiry date and warning period from settings."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.license_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)

        for record in self:
            if not record.expiry_date:
                record.expiry_status = 'no_expiry'
            elif record.expiry_date < today:
                record.expiry_status = 'expired'
            elif record.expiry_date <= warning_date:
                record.expiry_status = 'expiring'
            else:
                record.expiry_status = 'valid'

    @api.onchange('qualification_id', 'issue_date')
    def _onchange_calculate_expiry(self):
        """Calculate expiry date based on issue date and validity months.

        The expiry date is set to the last day of the month after adding
        the validity period.
        """
        for record in self:
            if record.issue_date and record.qualification_id and record.qualification_id.validity_months:  # type: ignore
                total_months = record.issue_date.month - 1 + record.qualification_id.validity_months  # type: ignore
                expiry_year = record.issue_date.year + (total_months // 12)
                expiry_month = (total_months % 12) + 1
                last_day = monthrange(expiry_year, expiry_month)[1]
                record.expiry_date = date(expiry_year, expiry_month, last_day)
            else:
                record.expiry_date = False
