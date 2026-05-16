# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Fleet aircraft module.

Purpose:
    Defines classes Aircraft for aircraft categories, aircraft types, aircraft records, maintenance awareness, and fleet dashboard data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training defines aircraft-type requirements.
"""
from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class Aircraft(models.Model):
    """Individual aircraft in the training fleet.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.aircraft``.
        _inherit: Odoo model(s) extended by this class: ``['mail.thread', 'mail.activity.mixin']``.
        _description (str): Human-readable model label, ``Aircraft``.

    Related:
        fs_training defines aircraft-type requirements.
        fs_scheduling and fs_flights use aircraft availability and total-hour data.
    """

    _name = 'fs.aircraft'
    _description = 'Aircraft'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'registration'

    # === Basic Information ===
    registration = fields.Char(
        string='Registration',
        required=True,
        tracking=True,
        help="Aircraft registration number (e.g., TS-APR, N12345).",
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    aircraft_type_id = fields.Many2one(
        comodel_name='fs.aircraft.type',
        string='Aircraft Type',
        required=True,
        tracking=True,
        ondelete='restrict',
        help="Make and model of the aircraft.",
    )
    category_id = fields.Many2one(
        comodel_name='fs.aircraft.category',
        string='Category',
        related='aircraft_type_id.category_id',
        store=True,
        readonly=True,
    )
    manufacturer = fields.Char(
        string='Manufacturer',
        related='aircraft_type_id.manufacturer',
        store=True,
        readonly=True,
    )
    category_code = fields.Char(
        string='Category Code',
        related='category_id.code',
        store=True,
    )

    # === Identification ===
    serial_number = fields.Char(
        string='Serial Number',
        help="Manufacturer's serial number.",
    )
    year_manufactured = fields.Char(
        string='Year Manufactured',
        size=4,
        help="Year the aircraft was manufactured (YYYY).",
    )

    # === Status ===
    status = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('in_use', 'In Use'),
            ('maintenance', 'In Maintenance'),
            ('grounded', 'Grounded'),
        ],
        string='Status',
        default='available',
        required=True,
        tracking=True,
        help="Current operational status of the aircraft.",
        group_expand="_read_group_status",
    )

    @api.model
    def _read_group_status(self, stages, domain):
        """Ensure all status columns are visible in Kanban even if empty.

        Args:
            stages: Grouped records supplied by Odoo read_group.
            domain: Odoo domain limiting the records considered by the operation.

        Returns:
            list: Values prepared for the Odoo view, search, or grouping API.
        """
        return [key for key, val in self.fields_get(['status'])['status']['selection']]
    status_reason = fields.Text(
        string='Status Reason',
        tracking=True,
        help="Reason for current status (especially for grounded/maintenance).",
    )
    status_color = fields.Integer(
        string='Status Color',
        compute='_compute_status_color',
    )
    is_airworthy = fields.Boolean(
        string='Airworthy',
        compute='_compute_is_airworthy',
        store=True,
        help="Aircraft is technically fit to fly. Operational assignment uses a separate field.",
    )
    is_available_for_assignment = fields.Boolean(
        string='Available for Assignment',
        compute='_compute_is_available_for_assignment',
        store=True,
        help="Aircraft can be assigned immediately to a new flight or simulator session.",
    )
    airworthiness_blocker = fields.Selection(
        selection=[
            ('maintenance', 'In Maintenance'),
            ('grounded', 'Grounded'),
        ],
        string='Airworthiness Blocker',
        compute='_compute_airworthiness_blocker',
        store=True,
    )
    has_operational_warning = fields.Boolean(
        string='Has Operational Warning',
        compute='_compute_operational_warning',
    )
    operational_warning = fields.Text(
        string='Operational Warning',
        compute='_compute_operational_warning',
    )

    # === Hours Tracking ===
    total_hours = fields.Float(
        string='Total Hours',
        default=0.0,
        tracking=True,
        help="Total flight hours (airframe/Hobbs time).",
    )
    # tach_time = fields.Float(
    #     string='Tach Time',
    #     default=0.0,
    #     help="Current tachometer reading.",
    # )
    hours_since_overhaul = fields.Float(
        string='Hours Since Overhaul',
        default=0.0,
        help="Engine hours since last major overhaul.",
    )
    last_flight_date = fields.Date(
        string='Last Flight Date',
        help="Date of the most recent flight.",
    )

    # === Maintenance ===
    last_maintenance_date = fields.Date(
        string='Last Maintenance',
        tracking=True,
    )
    next_maintenance_date = fields.Date(
        string='Next Maintenance Due Date',
        tracking=True,
    )
    maintenance_due_at_hours = fields.Float(
        string='Maintenance Due At (Hours)',
        help="Total airframe hours when next maintenance is due.",
    )
    remaining_maintenance_hours = fields.Float(
        string='Hours Remaining',
        compute='_compute_remaining_maintenance_hours',
        store=True,
        help="Remaining hours until next maintenance.",
    )
    maintenance_hour_status = fields.Selection(
        selection=[
            ('ok', 'OK'),
            ('due_soon', 'Due Soon'),
            ('overdue', 'Overdue'),
            ('not_configured', 'Not Configured'),
        ],
        string='Hour Warning',
        compute='_compute_maintenance_hour_status',
    )
    maintenance_date_status = fields.Selection(
        selection=[
            ('ok', 'OK'),
            ('due_soon', 'Due Soon'),
            ('overdue', 'Overdue'),
            ('not_configured', 'Not Configured'),
        ],
        string='Date Warning',
        compute='_compute_maintenance_date_status',
    )
    maintenance_status = fields.Selection(
        selection=[
            ('ok', 'OK'),
            ('due_soon', 'Due Soon'),
            ('overdue', 'Overdue'),
            ('not_configured', 'Not Configured'),
        ],
        string='Overall Maintenance Status',
        compute='_compute_maintenance_status',
        store=True,
    )

    # === Insurance & Certificates ===
    insurance_policy = fields.Char(
        string='Insurance Policy #',
    )
    insurance_expiry = fields.Date(
        string='Insurance Expiry',
        tracking=True,
    )
    cof_a_expiry = fields.Date(
        string='C of A Expiry',
        tracking=True,
        help="Certificate of Airworthiness expiry date.",
    )
    arc_expiry = fields.Date(
        string='ARC Expiry',
        tracking=True,
        help="Airworthiness Review Certificate expiry date.",
    )

    # === Location ===
    home_base = fields.Char(
        string='Home Base',
        help="ICAO code of home airport (e.g., DTTI).",
    )

    # === Images ===
    image = fields.Image(
        string='Photo',
        max_width=1920,
        max_height=1080,
    )
    image_128 = fields.Image(
        string='Thumbnail',
        related='image',
        max_width=128,
        max_height=128,
        store=True,
    )

    # === Administrative ===
    notes = fields.Text(
        string='Notes',
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
    )

    _registration_unique = models.Constraint(
        'UNIQUE(registration)',
        'Aircraft registration must be unique!',
    )

    @api.model
    def _normalize_registration_value(self, registration):
        """Normalize registrations server-side for imports and API writes."""
        if not registration:
            return registration
        return registration.strip().upper()

    @api.model
    def _normalize_write_vals(self, vals):
        """Apply fleet normalization rules to create/write values."""
        normalized = dict(vals)
        if 'registration' in normalized and normalized['registration']:
            normalized['registration'] = self._normalize_registration_value(normalized['registration'])
        return normalized

    @api.model
    def _get_maintenance_warning_hours(self):
        """Return the configured maintenance-hour warning threshold."""
        return float(
            self.env['ir.config_parameter'].sudo().get_param(
                'flight_school.maintenance_warning_hours',
                '5.0',
            )
        )

    @api.model
    def _get_maintenance_warning_days(self):
        """Return the configured maintenance-date warning threshold."""
        return int(
            self.env['ir.config_parameter'].sudo().get_param(
                'flight_school.maintenance_warning_days',
                '7',
            )
        )

    def _get_remaining_maintenance_hours_value(self):
        """Return remaining hours before the next maintenance event."""
        self.ensure_one()
        if self.maintenance_due_at_hours:
            return self.maintenance_due_at_hours - self.total_hours
        return 0.0

    def _get_maintenance_hour_status_value(self, warning_hours):
        """Return the hour-based maintenance warning state."""
        self.ensure_one()
        if not self.maintenance_due_at_hours:
            return 'not_configured'

        remaining_hours = self._get_remaining_maintenance_hours_value()
        if remaining_hours < 0:
            return 'overdue'
        if remaining_hours <= warning_hours:
            return 'due_soon'
        return 'ok'

    def _get_maintenance_date_status_value(self, today, warning_days):
        """Return the date-based maintenance warning state."""
        self.ensure_one()
        if not self.next_maintenance_date:
            return 'not_configured'

        days_until = (self.next_maintenance_date - today).days
        if days_until < 0:
            return 'overdue'
        if days_until <= warning_days:
            return 'due_soon'
        return 'ok'

    def _get_maintenance_status_value(self, hour_status, date_status):
        """Return the consolidated maintenance warning state."""
        self.ensure_one()
        configured_statuses = {hour_status, date_status} - {'not_configured'}
        if 'overdue' in configured_statuses:
            return 'overdue'
        if 'due_soon' in configured_statuses:
            return 'due_soon'
        if 'ok' in configured_statuses:
            return 'ok'
        return 'not_configured'

    def _get_operational_warning_parts(self, today=None):
        """Return non-blocking maintenance and document warning messages."""
        self.ensure_one()
        today = today or date.today()
        warning_date = today + timedelta(days=30)
        warnings = []

        maintenance_messages = {
            'overdue': _('Maintenance is overdue.'),
            'due_soon': _('Maintenance is due soon.'),
            'not_configured': _('Maintenance thresholds are not configured.'),
        }
        if self.maintenance_status in maintenance_messages:
            warnings.append(maintenance_messages[self.maintenance_status])

        document_labels = [
            (_('Insurance'), self.insurance_expiry),
            (_('Certificate of Airworthiness'), self.cof_a_expiry),
            (_('ARC'), self.arc_expiry),
        ]
        for label, expiry_date in document_labels:
            if not expiry_date:
                warnings.append(_('%(label)s expiry date is missing.', label=label))
            elif expiry_date < today:
                warnings.append(_('%(label)s has expired.', label=label))
            elif expiry_date <= warning_date:
                warnings.append(_('%(label)s expires within 30 days.', label=label))

        return warnings

    @api.depends('registration', 'aircraft_type_id.full_name')
    def _compute_display_name(self):
        """Compute display name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            # type: ignore[attr-defined]
            type_name = record.aircraft_type_id.full_name if record.aircraft_type_id else ''
            record.display_name = f"{record.registration} ({type_name})"

    @api.depends('status')
    def _compute_status_color(self):
        """Compute status color values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        color_map = {
            'available': 10,    # Green
            'in_use': 4,        # Blue
            'maintenance': 3,   # Yellow
            'grounded': 1,      # Red
        }
        for record in self:
            record.status_color = color_map.get(record.status or 'available', 0)

    @api.depends('status')
    def _compute_is_airworthy(self):
        """Compute is airworthy values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.is_airworthy = record.status not in ('maintenance', 'grounded')

    @api.depends('is_airworthy', 'status')
    def _compute_is_available_for_assignment(self):
        """Compute assignment availability values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.is_available_for_assignment = record.is_airworthy and record.status == 'available'

    @api.depends('status')
    def _compute_airworthiness_blocker(self):
        """Compute the blocking state that makes an aircraft non-airworthy."""
        for record in self:
            if record.status == 'maintenance':
                record.airworthiness_blocker = 'maintenance'
            elif record.status == 'grounded':
                record.airworthiness_blocker = 'grounded'
            else:
                record.airworthiness_blocker = False

    @api.depends(
        'maintenance_status',
        'insurance_expiry',
        'cof_a_expiry',
        'arc_expiry',
    )
    def _compute_operational_warning(self):
        """Compute non-blocking operational warning messages."""
        today = date.today()
        for record in self:
            warnings = record._get_operational_warning_parts(today=today)
            record.has_operational_warning = bool(warnings)
            record.operational_warning = '\n'.join(warnings) if warnings else False

    @api.depends('maintenance_due_at_hours', 'total_hours')
    def _compute_remaining_maintenance_hours(self):
        """Compute remaining maintenance hours values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.remaining_maintenance_hours = record._get_remaining_maintenance_hours_value()

    @api.depends('remaining_maintenance_hours')
    def _compute_maintenance_hour_status(self):
        """Compute maintenance hour status values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        warning_hours = self._get_maintenance_warning_hours()
        for record in self:
            record.maintenance_hour_status = record._get_maintenance_hour_status_value(warning_hours)

    @api.depends('next_maintenance_date')
    def _compute_maintenance_date_status(self):
        """Compute maintenance date status values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        today = date.today()
        warning_days = self._get_maintenance_warning_days()
        for record in self:
            record.maintenance_date_status = record._get_maintenance_date_status_value(today, warning_days)

    @api.depends('maintenance_hour_status', 'maintenance_date_status')
    def _compute_maintenance_status(self):
        """Compute maintenance status values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.maintenance_status = record._get_maintenance_status_value(
                record.maintenance_hour_status,
                record.maintenance_date_status,
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Normalize aircraft values before creation."""
        normalized_vals_list = [self._normalize_write_vals(vals) for vals in vals_list]
        return super().create(normalized_vals_list)

    def write(self, vals):
        """Normalize aircraft values before writing."""
        return super().write(self._normalize_write_vals(vals))

    @api.onchange('registration')
    def _onchange_registration_uppercase(self):
        """Update form values when registration uppercase changes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.registration:
            self.registration = self.registration.upper()

    @api.constrains('registration')
    def _check_registration_format(self):
        """Validate registration format business rules.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            UserError: If user-facing business validation fails.
        """
        for record in self:
            if record.registration and not record.registration.replace('-', '').isalnum():
                raise ValidationError(
                    _('Registration must contain only letters, numbers, and hyphens.'),
                )

    @api.constrains('year_manufactured')
    def _check_year_manufactured(self):
        """Validate year manufactured business rules.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            UserError: If user-facing business validation fails.
        """
        for record in self:
            if record.year_manufactured:
                if not record.year_manufactured.isdigit() or len(record.year_manufactured) != 4:
                    raise ValidationError(
                        _('Year Manufactured must be 4 numeric characters (YYYY).'),
                    )

    def _check_schedulable_aircraft(self, expected_simulator=None):
        """Ensure aircraft can be planned on a schedule.

        Scheduling is warning-based for maintenance/document issues. Only hard
        blockers such as grounded/maintenance states and simulator mismatches
        prevent planning.
        """
        blocker_labels = {
            'maintenance': _('in maintenance'),
            'grounded': _('grounded'),
        }
        for record in self:
            if not record.is_airworthy:
                raise ValidationError(
                    _(
                        "Aircraft '%(registration)s' cannot be scheduled because it is %(blocker)s.",
                        registration=record.registration,
                        blocker=blocker_labels.get(record.airworthiness_blocker, _('unavailable')),
                    ),
                )
            if expected_simulator is not None and bool(record.category_id.is_simulator) != bool(expected_simulator):
                raise ValidationError(
                    _(
                        "Aircraft '%(registration)s' does not match the selected mission type.",
                        registration=record.registration,
                    ),
                )

    def _check_dispatchable_aircraft(self, expected_simulator=None):
        """Ensure aircraft can be assigned immediately to a flight."""
        self._check_schedulable_aircraft(expected_simulator=expected_simulator)
        for record in self:
            if not record.is_available_for_assignment:
                raise ValidationError(
                    _(
                        "Aircraft '%(registration)s' is not currently available for assignment.",
                        registration=record.registration,
                    ),
                )

    @api.model
    def cron_refresh_aircraft_maintenance_status(self):
        """Refresh stored maintenance warning fields that depend on the current date."""
        records = self.search([])
        warning_hours = self._get_maintenance_warning_hours()
        warning_days = self._get_maintenance_warning_days()
        today = date.today()
        for record in records:
            hour_status = record._get_maintenance_hour_status_value(warning_hours)
            date_status = record._get_maintenance_date_status_value(today, warning_days)
            record.sudo().write({
                'remaining_maintenance_hours': record._get_remaining_maintenance_hours_value(),
                'maintenance_status': record._get_maintenance_status_value(hour_status, date_status),
            })

    def action_set_available(self):
        """Set aircraft status to available.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.write({'status': 'available', 'status_reason': False})

    def action_set_maintenance(self):
        """Set aircraft status to in maintenance.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.write({'status': 'maintenance'})

    def action_set_grounded(self):
        """Set aircraft status to grounded.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.write({'status': 'grounded'})

    def unlink(self):
        """Delete records after enforcing Flight School business safeguards.

        Returns:
            bool: True when Odoo successfully deletes the records.

        Raises:
            UserError: If user-facing business validation fails.
        """
        for record in self:
            if record.total_hours > 0:
                raise UserError(
                    _(
                        "Cannot delete aircraft '%(registration)s' with flight history. "
                        "Archive it instead by unchecking 'Active'.",
                        registration=record.registration,
                    )
                )
        return super().unlink()
