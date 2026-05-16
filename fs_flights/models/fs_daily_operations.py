# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Flights fs daily operations module.

Purpose:
    Defines classes FsDailyOperations for daily operations boards, simulator operations, flight execution logs, cancellation workflows, schedule imports, and hour distribution.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from datetime import timedelta

from odoo import _, api, fields, models


class FsDailyOperations(models.Model):
    """Dashboard for daily flight operations monitoring.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.daily.operations``.
        _description (str): Human-readable model label, ``Daily Operations Dashboard``.

    Related:
        fs_scheduling provides planned flights.
        fs_training enrollments receive completed-hour updates.
    """

    _name = 'fs.daily.operations'
    _description = 'Daily Operations Dashboard'
    _rec_name = 'date'
    _order = 'date desc'

    _date_unique = models.Constraint(
        'unique(date)',
        'Only one operations board can exist per date.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create records while applying module-specific defaults and side effects.

        Args:
            vals_list: List of value dictionaries passed to the multi-record create method.

        Returns:
            models.Model: Odoo recordset returned by the ORM.
        """
        records = super().create(vals_list)
        for record in records:
            if record.date:
                # Link existing flights (NOT simulators) for this date to the new board
                flights = (
                    self.env['fs.flight']
                    .search([
                        ('date', '=', record.date),
                        ('daily_ops_id', '=', False),
                    ])
                    .filtered(
                        lambda flight: not flight.aircraft_id.category_id.is_simulator,
                    )  # type: ignore
                )

                if flights:
                    flights.write({'daily_ops_id': record.id})
        return records

    date = fields.Date(
        string='Date',
        default=fields.Date.today,
    )
    date_display = fields.Char(
        string='Date Display',
        compute='_compute_date_display',
    )
    name = fields.Char(compute='_compute_name')

    @api.depends('date')
    def _compute_name(self):
        """Compute name values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.name = (
                _("Operations Board - %s") % record.date
                if record.date
                else _("Operations Board")
            )

    @api.depends('date')
    def _compute_date_display(self):
        """Compute date display values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        import calendar
        for record in self:
            if record.date:
                record.date_display = (
                    f"{calendar.day_name[record.date.weekday()]}, "
                    f"{record.date.day} {calendar.month_name[record.date.month]}"
                )
            else:
                record.date_display = ''

    # === Summary KPIs ===
    flights_scheduled = fields.Integer(
        string='Scheduled',
        compute='_compute_kpis',
        store=True,
    )
    flights_in_progress = fields.Integer(
        string='In Progress',
        compute='_compute_kpis',
        store=True,
    )
    flights_completed = fields.Integer(
        string='Done',
        compute='_compute_kpis',
        store=True,
    )
    flights_cancelled = fields.Integer(
        string='Cancelled',
        compute='_compute_kpis',
        store=True,
    )
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_kpis',
        store=True,
    )
    total_hours_display = fields.Char(
        string='Total Hours Display',
        compute='_compute_kpis',
        store=True,
    )
    last_add_callsign = fields.Char(
        string='Last ADD',
        compute='_compute_last_add_callsign',
        help="Last used callsign for added missions (above threshold)",
    )

    # === UI Fields ===
    fullscreen_dummy = fields.Boolean(
        string='Fullscreen Toggle',
        store=False,
    )
    refresh_dummy = fields.Boolean(
        string='Refresh Button',
        store=False,
    )
    carousel_control_dummy = fields.Boolean(
        string='Carousel Control',
        store=False,
    )

    # === Available Aircraft Footer ===
    available_aircraft_html = fields.Html(
        string='Available Aircraft',
        compute='_compute_available_aircraft',
        sanitize=False,
    )

    # === Cancellation Breakdown ===
    cancellation_summary_html = fields.Html(
        string='Cancellations',
        compute='_compute_cancellation_summary',
        sanitize=False,
    )

    # === Flight logs for Today (Renamed to Flights) ===
    flight_log_ids = fields.One2many(
        comodel_name='fs.flight',
        inverse_name='daily_ops_id',
        string='Flight Logs',
    )
    flight_log_count = fields.Integer(
        string='Flight Count',
        compute='_compute_flight_log_count',
        store=True,
    )

    @api.depends('flight_log_ids')
    def _compute_flight_log_count(self):
        """Compute flight log count values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.flight_log_count = len(record.flight_log_ids)

    # === Pagination for Carousel ===
    def _default_page_size(self):
        """Return the default page size value.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
        """
        value = self.env['ir.config_parameter'].sudo().get_param(
            'flight_school.operations_page_size', '10',
        )
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 10

    page_size = fields.Integer(
        string='Flights per Page',
        default=_default_page_size,
    )
    current_page = fields.Integer(
        string='Current Page',
        default=0,
    )
    total_pages = fields.Integer(
        string='Total Pages',
        compute='_compute_pagination',
    )
    page_info = fields.Char(
        string='Page Info',
        compute='_compute_pagination',
    )
    paginated_flight_log_ids = fields.Many2many(
        comodel_name='fs.flight',
        string='Paginated Flight Logs',
        compute='_compute_paginated_flights',
        relation='fs_daily_ops_paginated_flights_rel',
    )

    @api.depends(
        'flight_log_ids',
        'flight_log_ids.status',
        'flight_log_ids.actual_duration',
        'flight_log_ids.aircraft_id',
    )
    def _compute_kpis(self):
        """Compute summary KPIs for today's flights.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            # Filter non-simulators
            logs = record.flight_log_ids.filtered(
                lambda flight: not flight.aircraft_id.category_id.is_simulator,
            )  # type: ignore

            record.flights_scheduled = len(
                logs.filtered_domain([('status', '=', 'scheduled')]),
            )
            record.flights_in_progress = len(
                logs.filtered_domain([('status', '=', 'in_progress')]),
            )
            record.flights_completed = len(
                logs.filtered_domain([('status', '=', 'done')]),
            )
            record.flights_cancelled = len(
                logs.filtered_domain([('status', '=', 'cancelled')]),
            )

            # Total hours from completed flights
            done_logs = logs.filtered_domain([('status', '=', 'done')])
            total = sum(log.actual_duration or 0.0 for log in done_logs)
            record.total_hours = total

            # Format as HH:MM
            hours = int(total)
            minutes = int((total - hours) * 60)
            record.total_hours_display = f"{hours:02d}:{minutes:02d}"

    @api.depends('date')
    def _compute_last_add_callsign(self):
        """Compute the last added callsign for the whole year.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if not record.date:
                record.last_add_callsign = '-'
                continue

            # Year range
            start_year = record.date.replace(month=1, day=1)
            end_year = record.date.replace(month=12, day=31)

            # Search globally in fs.flight for this year (excluding simulators)
            domain = [
                ('date', '>=', start_year),
                ('date', '<=', end_year),
                ('aircraft_id.category_id.is_simulator', '=', False),
                ('callsign', '!=', False),
            ]
            flight_data = self.env['fs.flight'].search_read(domain, ['callsign'])

            # Logic to find max callsign
            icp = self.env['ir.config_parameter'].sudo()
            threshold = int(
                icp.get_param('flight_school.first_added_mission_number', '7000'),
            )
            prefix = str(icp.get_param('flight_school.mission_callsign_prefix', 'ABS'))

            max_num = -1
            for data in flight_data:
                callsign = data['callsign']
                if (
                    isinstance(callsign, str)
                    and callsign.startswith(prefix)
                    and len(callsign) > len(prefix)
                ):
                    suffix = callsign[len(prefix):]
                    if suffix.isdigit():
                        value = int(suffix)
                        if value >= threshold and value > max_num:
                            max_num = value

            if max_num != -1:
                record.last_add_callsign = f"{prefix}{max_num}"
            else:
                record.last_add_callsign = '-'

    @api.depends('flight_log_count', 'page_size')
    def _compute_pagination(self):
        """Compute pagination info.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            page_size = max(record.page_size or 10, 1)
            total_count = record.flight_log_count
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            record.total_pages = total_pages
            current = max(0, min(record.current_page, total_pages - 1))
            record.page_info = f"Page {current + 1} of {total_pages}"

    @api.depends('flight_log_ids', 'current_page', 'page_size')
    def _compute_paginated_flights(self):
        """Get the flights for the current page.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            page_size = max(record.page_size or 10, 1)
            current_page = record.current_page or 0
            total_pages = record.total_pages or 1

            # Ensure current_page is within bounds
            current_page = max(0, min(current_page, total_pages - 1))

            start_idx = current_page * page_size
            end_idx = start_idx + page_size

            # Slice the flight logs
            all_logs = record.flight_log_ids
            paginated = all_logs[start_idx:end_idx] if all_logs else all_logs
            record.paginated_flight_log_ids = paginated

    @api.depends('date')
    def _compute_available_aircraft(self):
        """Compute available aircraft (not in flight, not in maintenance).

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            today = record.date or fields.Date.context_today(self)

            # Get aircraft currently in flight
            in_flight_logs = self.env['fs.flight'].search([
                ('date', '=', today),
                ('status', '=', 'in_progress'),
            ])
            in_flight_aircraft_ids = in_flight_logs.mapped('aircraft_id.id')

            # Get aircraft that can be assigned immediately.
            available = self.env['fs.aircraft'].search([
                ('is_available_for_assignment', '=', True),
                ('id', 'not in', in_flight_aircraft_ids),
                ('category_id.is_simulator', '=', False),
            ])

            html = '<div class="d-flex flex-wrap gap-2 justify-content-center">'
            # Use read() to iterate over dictionaries and avoid field access warnings.
            for ac_data in available.read(['registration']):
                html += (
                    f'<span class="badge bg-success fs-6 text-white">'
                    f'{ac_data["registration"]}</span>'
                )
            if not available:
                html += '<span class="text-muted">No aircraft available</span>'
            html += '</div>'
            record.available_aircraft_html = html

    @api.depends('date')
    def _compute_cancellation_summary(self):
        """Show cancellation reasons breakdown.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            today = record.date or fields.Date.context_today(self)
            cancelled = self.env['fs.flight'].search([
                ('date', '=', today),
                ('status', '=', 'cancelled'),
                ('aircraft_id.category_id.is_simulator', '=', False),
            ])

            if not cancelled:
                record.cancellation_summary_html = (
                    '<span class="text-muted">No cancellations</span>'
                )
                continue

            # Group by reason
            reasons: dict = {}
            # Use read() to iterate over dictionaries
            for log_data in cancelled.read([
                'cancellation_code',
                'cancellation_reason_id',
            ]):
                reason_code = log_data['cancellation_code'] or 'N/A'
                # M2O field in read() returns (id, displayName)
                reason_name = (
                    log_data['cancellation_reason_id'][1]
                    if log_data['cancellation_reason_id']
                    else 'Unknown'
                )
                if reason_code not in reasons:
                    reasons[reason_code] = {'name': reason_name, 'count': 0}
                reasons[reason_code]['count'] += 1

            html = '<div class="d-flex flex-wrap gap-1">'
            for code, data in reasons.items():
                html += f'<span class="badge bg-danger">{code}: {data["count"]}</span>'
            html += '</div>'
            record.cancellation_summary_html = html

    # === Actions ===

    def action_previous_day(self):
        """Go to previous day.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        today = self.date or fields.Date.context_today(self)
        target_date = today - timedelta(days=1)
        return self._open_date(target_date)

    def action_next_day(self):
        """Go to next day.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        today = self.date or fields.Date.context_today(self)
        target_date = today + timedelta(days=1)
        return self._open_date(target_date)

    def _open_date(self, target_date):
        """Find or create record for target date and open it.

        Args:
            target_date: Value supplied by Odoo or the calling workflow.

        Returns:
            dict: Structured data or an Odoo action dictionary produced by the workflow.
        """
        record = self.search([('date', '=', target_date)], limit=1)
        if not record:
            record = self.create({'date': target_date})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fs.daily.operations',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'main',  # Keep existing target
            'context': {'form_view_initial_mode': 'edit'},  # Keep edit mode
        }

    def action_add_flight(self):
        """Open add flight wizard.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': _('Add Flight'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.add.flight.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_date': self.date or fields.Date.context_today(self)},
        }

    def action_refresh(self):
        """Refresh the operations board.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_open_operations_board(self):
        """Open the operations board in full view.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        today = fields.Date.context_today(self)
        record = self.search([('date', '=', today)], limit=1)
        if not record:
            record = self.create({'date': today})

        return {
            'name': _('Daily Operations'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.daily.operations',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'fullscreen',
            'context': {'form_view_initial_mode': 'readonly'},
        }

    # === Pagination Navigation ===

    def action_next_page(self):
        """Go to next page of flights (infinite loop).

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.total_pages > 1:
            # If on last page, go to first (0), else next
            if self.current_page >= self.total_pages - 1:
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
        return self._reload_view()

    def action_prev_page(self):
        """Go to previous page of flights (infinite loop).

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.total_pages > 1:
            # If on first page, go to last, else previous
            if self.current_page <= 0:
                self.current_page = self.total_pages - 1
            else:
                self.current_page = self.current_page - 1
        return self._reload_view()

    def action_first_page(self):
        """Go to first page of flights.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        self.current_page = 0
        return self._reload_view()

    def action_last_page(self):
        """Go to last page of flights.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        self.current_page = self.total_pages - 1
        return self._reload_view()

    def _reload_view(self):
        """Helper to reload the current view without closing it.

        Returns:
            bool: True or False according to the validation or lookup result.
        """
        # returning True forces the web client to reload the form data in-place
        return True
