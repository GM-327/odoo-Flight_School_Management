# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from calendar import day_name, month_name
from datetime import timedelta

from odoo import _, api, fields, models


class FsSimulatorOperations(models.Model):
    """Dashboard for daily simulator operations monitoring."""

    _name = 'fs.simulator.operations'
    _description = 'Simulator Operations Dashboard'
    _rec_name = 'date'
    _order = 'date desc'

    _date_unique = models.Constraint(
        'unique(date)',
        'Only one simulator operations board can exist per date.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.date:
                # Link existing simulator flights for this date to the new board
                flights = self.env['fs.flight'].search([
                    ('date', '=', record.date),
                    ('simulator_ops_id', '=', False),
                ]).filtered(lambda f: f.aircraft_id.category_id.is_simulator)  # type: ignore

                if flights:
                    flights.write({'simulator_ops_id': record.id})
        return records

    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
    )
    date_display = fields.Char(string='Date Display', compute='_compute_date_display')
    name = fields.Char(compute='_compute_name')

    @api.depends('date')
    def _compute_name(self):
        for record in self:
            record.name = (
                _("Simulator Board - %s") % record.date
                if record.date
                else _("Simulator Board")
            )

    @api.depends('date')
    def _compute_date_display(self):
        for record in self:
            if record.date:
                record.date_display = (
                    f"{day_name[record.date.weekday()]}, "
                    f"{record.date.day} {month_name[record.date.month]}"
                )
            else:
                record.date_display = ''

    # === Summary KPIs ===
    sessions_scheduled = fields.Integer(
        string='Scheduled',
        compute='_compute_kpis',
        store=True,
    )
    sessions_in_progress = fields.Integer(
        string='In Progress',
        compute='_compute_kpis',
        store=True,
    )
    sessions_completed = fields.Integer(
        string='Done',
        compute='_compute_kpis',
        store=True,
    )
    sessions_cancelled = fields.Integer(
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
    last_sim_callsign = fields.Char(
        string='Last SIM Callsign',
        compute='_compute_last_sim_callsign',
        help="Last used simulator callsign for the current year (e.g., SIM0042)",
    )

    # === UI Fields ===
    fullscreen_dummy = fields.Boolean(string='Fullscreen Toggle', store=False)
    refresh_dummy = fields.Boolean(string='Refresh Button', store=False)
    carousel_control_dummy = fields.Boolean(string='Carousel Control', store=False)

    # === Available Simulators Footer ===
    available_simulators_html = fields.Html(
        string='Available Simulators',
        compute='_compute_available_simulators',
        sanitize=False,
    )

    # === Session logs for Today ===
    session_ids = fields.One2many(
        comodel_name='fs.flight',
        inverse_name='simulator_ops_id',
        string='Simulator Sessions',
    )
    session_count = fields.Integer(
        string='Session Count',
        compute='_compute_session_count',
        store=True,
    )

    @api.depends('session_ids')
    def _compute_session_count(self):
        for record in self:
            record.session_count = len(record.session_ids)

    # === Pagination for Carousel ===
    def _default_page_size(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'flight_school.operations_page_size', '10',
        )
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 10

    page_size = fields.Integer(
        string='Sessions per Page',
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
    paginated_session_ids = fields.Many2many(
        comodel_name='fs.flight',
        string='Paginated Sessions',
        compute='_compute_paginated_sessions',
        relation='fs_sim_ops_paginated_sessions_rel',
    )

    @api.depends('session_ids', 'session_ids.status', 'session_ids.actual_duration', 'session_ids.aircraft_id')
    def _compute_kpis(self):
        """Compute summary KPIs for today's simulator sessions."""
        for record in self:
            # Filter simulators only
            logs = record.session_ids.filtered(lambda l: l.aircraft_id.category_id.is_simulator)  # type: ignore

            record.sessions_scheduled = len(logs.filtered_domain([('status', '=', 'scheduled')]))
            record.sessions_in_progress = len(logs.filtered_domain([('status', '=', 'in_progress')]))
            record.sessions_completed = len(logs.filtered_domain([('status', '=', 'done')]))
            record.sessions_cancelled = len(logs.filtered_domain([('status', '=', 'cancelled')]))

            # Total hours from completed sessions
            done_logs = logs.filtered_domain([('status', '=', 'done')])
            total = sum(session.actual_duration or 0.0 for session in done_logs)
            record.total_hours = total

            # Format as HH:MM
            hours = int(total)
            minutes = int((total - hours) * 60)
            record.total_hours_display = f"{hours:02d}:{minutes:02d}"

    @api.depends('date')
    def _compute_last_sim_callsign(self):
        """Compute the last used simulator callsign for the current year.

        Simulator callsigns follow the format SIM0001, SIM0002, etc.
        They increment normally (no threshold like ADD missions for flights).
        """
        for record in self:
            if not record.date:
                record.last_sim_callsign = '-'
                continue

            # Year range
            start_year = record.date.replace(month=1, day=1)
            end_year = record.date.replace(month=12, day=31)

            # Search for SIM callsigns in fs.flight for this year
            domain = [
                ('date', '>=', start_year),
                ('date', '<=', end_year),
                ('callsign', '=like', 'SIM%'),
            ]
            flight_data = self.env['fs.flight'].search_read(domain, ['callsign'])

            # Find max SIM callsign number
            max_num = -1
            for data in flight_data:
                c = data['callsign']
                if isinstance(c, str) and c.startswith('SIM') and len(c) > 3:
                    suffix = c[3:]  # Remove 'SIM' prefix
                    if suffix.isdigit():
                        val = int(suffix)
                        if val > max_num:
                            max_num = val

            if max_num != -1:
                record.last_sim_callsign = f"SIM{max_num:04d}"
            else:
                record.last_sim_callsign = '-'

    @api.depends('session_count', 'page_size')
    def _compute_pagination(self):
        """Compute pagination info."""
        for record in self:
            page_size = record.page_size or 10
            total_count = record.session_count
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            record.total_pages = total_pages
            current = min(record.current_page, total_pages - 1)
            record.page_info = f"Page {current + 1} of {total_pages}"

    @api.depends('session_ids', 'current_page', 'page_size')
    def _compute_paginated_sessions(self):
        """Get the sessions for the current page."""
        for record in self:
            page_size = record.page_size or 10
            current_page = record.current_page or 0
            total_pages = record.total_pages or 1

            current_page = max(0, min(current_page, total_pages - 1))

            start_idx = current_page * page_size
            end_idx = start_idx + page_size

            all_logs = record.session_ids
            paginated = all_logs[start_idx:end_idx] if all_logs else all_logs
            record.paginated_session_ids = paginated

    @api.depends('date')
    def _compute_available_simulators(self):
        """Compute available simulators (not in use)."""
        for record in self:
            today = record.date or fields.Date.context_today(self)

            # Get simulators currently in use
            in_use_logs = self.env['fs.flight'].search([
                ('date', '=', today),
                ('status', '=', 'in_progress'),
                ('aircraft_id.category_id.is_simulator', '=', True),
            ])
            in_use_ids = in_use_logs.mapped('aircraft_id.id')

            # Get available simulators
            available = self.env['fs.aircraft'].search([
                ('is_airworthy', '=', True),
                ('status', '=', 'available'),
                ('id', 'not in', in_use_ids),
                ('category_id.is_simulator', '=', True),
            ])

            html = '<div class="d-flex flex-wrap gap-2 justify-content-center">'
            for ac_data in available.read(['registration']):
                html += f'<span class="badge bg-info fs-6 text-white">{ac_data["registration"]}</span>'
            if not available:
                html += '<span class="text-muted">No simulators available</span>'
            html += '</div>'
            record.available_simulators_html = html

    # === Actions ===

    def action_previous_day(self):
        """Go to previous day."""
        self.ensure_one()
        today = self.date or fields.Date.context_today(self)
        target_date = today - timedelta(days=1)
        return self._open_date(target_date)

    def action_next_day(self):
        """Go to next day."""
        self.ensure_one()
        today = self.date or fields.Date.context_today(self)
        target_date = today + timedelta(days=1)
        return self._open_date(target_date)

    def _open_date(self, target_date):
        """Find or create record for target date and open it."""
        record = self.search([('date', '=', target_date)], limit=1)
        if not record:
            record = self.create({'date': target_date})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fs.simulator.operations',
            'res_id': record.id,
            'view_mode': 'form',
            'target': 'main',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_add_session(self):
        """Open add simulator session wizard."""
        return {
            'name': _('Add Simulator Session'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.add.sim.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_date': self.date or fields.Date.context_today(self),
                'default_is_simulator': True,
            },
        }

    def action_refresh(self):
        """Refresh the simulator board."""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # === Pagination Navigation ===

    def action_next_page(self):
        """Go to next page of sessions (infinite loop)."""
        self.ensure_one()
        if self.total_pages > 1:
            if self.current_page >= self.total_pages - 1:
                self.current_page = 0
            else:
                self.current_page = self.current_page + 1
        return self._reload_view()

    def action_prev_page(self):
        """Go to previous page of sessions (infinite loop)."""
        self.ensure_one()
        if self.total_pages > 1:
            if self.current_page <= 0:
                self.current_page = self.total_pages - 1
            else:
                self.current_page = self.current_page - 1
        return self._reload_view()

    def action_first_page(self):
        """Go to first page of sessions."""
        self.ensure_one()
        self.current_page = 0
        return self._reload_view()

    def action_last_page(self):
        """Go to last page of sessions."""
        self.ensure_one()
        self.current_page = self.total_pages - 1
        return self._reload_view()

    def _reload_view(self):
        """Helper to reload the current view without closing it."""
        return True
