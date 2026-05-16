# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Fleet fs fleet dashboard module.

Purpose:
    Defines classes FsFleetDashboard for aircraft categories, aircraft types, aircraft records, maintenance awareness, and fleet dashboard data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training defines aircraft-type requirements.
"""
from datetime import date, timedelta
import json
from odoo import api, fields, models


class FsFleetDashboard(models.TransientModel):
    """Dashboard for Fleet module - provides KPIs and quick actions.

    Uses TransientModel to create temporary records in database.
    Records are automatically cleaned up by Odoo's garbage collection.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.fleet.dashboard``.
        _description (str): Human-readable model label, ``Fleet Dashboard``.

    Related:
        fs_training defines aircraft-type requirements.
        fs_scheduling and fs_flights use aircraft availability and total-hour data.
    """

    _name = 'fs.fleet.dashboard'
    _description = 'Fleet Dashboard'

    name = fields.Char(string='Name', default='Fleet Dashboard')

    # === Graph Data ===
    status_distribution = fields.Text(
        string='Status Distribution Graph',
        compute='_compute_fleet_graph_data',
    )
    type_distribution = fields.Text(
        string='Type Distribution Graph',
        compute='_compute_fleet_graph_data',
    )

    # === Summary KPIs ===
    fleet_total = fields.Integer(
        string='Total Fleet Size',
        compute='_compute_summary_kpis',
    )
    fleet_availability = fields.Float(
        string='Fleet Availability (%)',
        compute='_compute_summary_kpis',
    )

    # === Aircraft Status KPIs ===
    aircraft_total = fields.Integer(
        string='Total Aircraft',
        compute='_compute_aircraft_kpis',
    )
    aircraft_available = fields.Integer(
        string='Available',
        compute='_compute_aircraft_kpis',
    )
    aircraft_in_use = fields.Integer(
        string='In Use',
        compute='_compute_aircraft_kpis',
    )
    aircraft_maintenance = fields.Integer(
        string='In Maintenance',
        compute='_compute_aircraft_kpis',
    )
    aircraft_grounded = fields.Integer(
        string='Grounded',
        compute='_compute_aircraft_kpis',
    )

    # === Maintenance KPIs ===
    maintenance_overdue = fields.Integer(
        string='Maintenance Overdue',
        compute='_compute_maintenance_kpis',
    )
    maintenance_due_soon = fields.Integer(
        string='Maintenance Due Soon',
        compute='_compute_maintenance_kpis',
    )

    # === Certificate KPIs ===
    cert_expired = fields.Integer(
        string='Expired Certificates',
        compute='_compute_certificate_kpis',
    )
    cert_expiring = fields.Integer(
        string='Certs Expiring Soon',
        compute='_compute_certificate_kpis',
    )

    @api.model
    def _get_group_count_map(self, field_name, domain=None):
        """Return grouped counts for a field as a plain dictionary."""
        grouped_rows = self.env['fs.aircraft']._read_group(
            domain or [],
            groupby=[field_name],
            aggregates=['__count'],
        )
        return {key: count for key, count in grouped_rows}

    def _compute_summary_kpis(self):
        """Compute top-level summary statistics.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        Aircraft = self.env['fs.aircraft']
        status_counts = self._get_group_count_map('status')
        total = Aircraft.search_count([])
        for record in self:
            record.fleet_total = total
            available = status_counts.get('available', 0)
            record.fleet_availability = (available / total * 100) if total > 0 else 100.0

    def _compute_aircraft_kpis(self):
        """Compute aircraft status statistics.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        status_counts = self._get_group_count_map('status')
        for record in self:
            record.aircraft_total = sum(status_counts.values())
            record.aircraft_available = status_counts.get('available', 0)
            record.aircraft_in_use = status_counts.get('in_use', 0)
            record.aircraft_maintenance = status_counts.get('maintenance', 0)
            record.aircraft_grounded = status_counts.get('grounded', 0)

    def _compute_maintenance_kpis(self):
        """Compute maintenance alert statistics.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        maintenance_counts = self._get_group_count_map('maintenance_status')
        for record in self:
            record.maintenance_overdue = maintenance_counts.get('overdue', 0)
            record.maintenance_due_soon = maintenance_counts.get('due_soon', 0)

    def _compute_certificate_kpis(self):
        """Compute certificate expiry statistics.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        Aircraft = self.env['fs.aircraft']
        today = date.today()
        warning_date = today + timedelta(days=30)
        for record in self:
            # Expired: any of insurance, C of A, or ARC expired
            record.cert_expired = Aircraft.search_count([
                '|', '|',
                ('insurance_expiry', '<', today),
                ('cof_a_expiry', '<', today),
                ('arc_expiry', '<', today),
            ])
            # Expiring soon: within 30 days but not expired
            record.cert_expiring = Aircraft.search_count([
                '|', '|',
                '&', ('insurance_expiry', '>=', today), ('insurance_expiry', '<=', warning_date),
                '&', ('cof_a_expiry', '>=', today), ('cof_a_expiry', '<=', warning_date),
                '&', ('arc_expiry', '>=', today), ('arc_expiry', '<=', warning_date),
            ])

    def _compute_fleet_graph_data(self):
        """Compute fleet distribution graph data.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        Aircraft = self.env['fs.aircraft']
        status_counts = self._get_group_count_map('status')

        # Status distribution
        status_data = [
            {'label': 'Available', 'value': status_counts.get('available', 0), 'type': 'future'},
            {'label': 'In Use', 'value': status_counts.get('in_use', 0), 'type': 'future'},
            {'label': 'Maintenance', 'value': status_counts.get('maintenance', 0), 'type': 'past'},
            {'label': 'Grounded', 'value': status_counts.get('grounded', 0), 'type': 'past'},
        ]

        # Type distribution (by manufacturer)
        type_data = []
        # Group by manufacturer
        grouped_data = Aircraft._read_group([], groupby=['manufacturer'], aggregates=['__count'])
        for manufacturer, count in grouped_data:
            label = manufacturer or 'Unknown'
            type_data.append({
                'label': label,
                'value': count,
                'type': 'future'
            })

        for record in self:
            record.status_distribution = json.dumps([{
                'values': status_data,
                'key': 'Aircraft by Status',
            }])
            record.type_distribution = json.dumps([{
                'values': type_data,
                'key': 'Aircraft by Manufacturer',
            }])

    # === Action Methods ===
    def action_view_aircraft(self):
        """Open all aircraft.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'All Aircraft',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'kanban,list,form',
        }

    def action_view_aircraft_available(self):
        """Open available aircraft.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Available Aircraft',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'kanban,list,form',
            'domain': [('status', '=', 'available')],
        }

    def action_view_aircraft_in_use(self):
        """Open aircraft in use.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Aircraft In Use',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,kanban,form',
            'domain': [('status', '=', 'in_use')],
        }

    def action_view_aircraft_maintenance(self):
        """Open aircraft in maintenance.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Aircraft In Maintenance',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'maintenance')],
        }

    def action_view_aircraft_grounded(self):
        """Open grounded aircraft.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Grounded Aircraft',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'grounded')],
        }

    def action_view_maintenance_overdue(self):
        """Open aircraft with overdue maintenance.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Maintenance Overdue',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('maintenance_status', '=', 'overdue')],
        }

    def action_view_maintenance_due_soon(self):
        """Open aircraft with maintenance due soon.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Maintenance Due Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('maintenance_status', '=', 'due_soon')],
        }

    def action_view_cert_expired(self):
        """Open aircraft with expired certificates.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        today = date.today()
        return {
            'name': 'Expired Certificates',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [
                '|', '|',
                ('insurance_expiry', '<', today),
                ('cof_a_expiry', '<', today),
                ('arc_expiry', '<', today),
            ],
        }

    def action_view_cert_expiring(self):
        """Open aircraft with certificates expiring soon.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        today = date.today()
        warning_date = today + timedelta(days=30)
        return {
            'name': 'Certificates Expiring Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [
                '|', '|',
                '&', ('insurance_expiry', '>=', today), ('insurance_expiry', '<=', warning_date),
                '&', ('cof_a_expiry', '>=', today), ('cof_a_expiry', '<=', warning_date),
                '&', ('arc_expiry', '>=', today), ('arc_expiry', '<=', warning_date),
            ],
        }
