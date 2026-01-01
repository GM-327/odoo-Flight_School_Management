# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import date, timedelta
import json
from odoo import api, fields, models


class FsFleetDashboard(models.TransientModel):
    """Dashboard for Fleet module - provides KPIs and quick actions.
    
    Uses TransientModel to create temporary records in database.
    Records are automatically cleaned up by Odoo's garbage collection.
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

    def _compute_summary_kpis(self):
        """Compute top-level summary statistics."""
        Aircraft = self.env['fs.aircraft']
        for record in self:
            total = Aircraft.search_count([])
            available = Aircraft.search_count([('status', '=', 'available')])
            record.fleet_total = total
            record.fleet_availability = (available / total * 100) if total > 0 else 100.0

    def _compute_aircraft_kpis(self):
        """Compute aircraft status statistics."""
        Aircraft = self.env['fs.aircraft']
        for record in self:
            record.aircraft_total = Aircraft.search_count([])
            record.aircraft_available = Aircraft.search_count([
                ('status', '=', 'available'),
            ])
            record.aircraft_in_use = Aircraft.search_count([
                ('status', '=', 'in_use'),
            ])
            record.aircraft_maintenance = Aircraft.search_count([
                ('status', '=', 'maintenance'),
            ])
            record.aircraft_grounded = Aircraft.search_count([
                ('status', '=', 'grounded'),
            ])

    def _compute_maintenance_kpis(self):
        """Compute maintenance alert statistics."""
        Aircraft = self.env['fs.aircraft']
        for record in self:
            record.maintenance_overdue = Aircraft.search_count([
                ('maintenance_status', '=', 'overdue'),
            ])
            record.maintenance_due_soon = Aircraft.search_count([
                ('maintenance_status', '=', 'due_soon'),
            ])

    def _compute_certificate_kpis(self):
        """Compute certificate expiry statistics."""
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
        """Compute fleet distribution graph data."""
        Aircraft = self.env['fs.aircraft']
        
        # Status distribution
        status_data = [
            {'label': 'Available', 'value': Aircraft.search_count([('status', '=', 'available')]), 'type': 'future'},
            {'label': 'In Use', 'value': Aircraft.search_count([('status', '=', 'in_use')]), 'type': 'future'},
            {'label': 'Maintenance', 'value': Aircraft.search_count([('status', '=', 'maintenance')]), 'type': 'past'},
            {'label': 'Grounded', 'value': Aircraft.search_count([('status', '=', 'grounded')]), 'type': 'past'},
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
        """Open all aircraft."""
        return {
            'name': 'All Aircraft',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'kanban,list,form',
        }

    def action_view_aircraft_available(self):
        """Open available aircraft."""
        return {
            'name': 'Available Aircraft',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'kanban,list,form',
            'domain': [('status', '=', 'available')],
        }

    def action_view_aircraft_in_use(self):
        """Open aircraft in use."""
        return {
            'name': 'Aircraft In Use',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,kanban,form',
            'domain': [('status', '=', 'in_use')],
        }

    def action_view_aircraft_maintenance(self):
        """Open aircraft in maintenance."""
        return {
            'name': 'Aircraft In Maintenance',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'maintenance')],
        }

    def action_view_aircraft_grounded(self):
        """Open grounded aircraft."""
        return {
            'name': 'Grounded Aircraft',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'grounded')],
        }

    def action_view_maintenance_overdue(self):
        """Open aircraft with overdue maintenance."""
        return {
            'name': 'Maintenance Overdue',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('maintenance_status', '=', 'overdue')],
        }

    def action_view_maintenance_due_soon(self):
        """Open aircraft with maintenance due soon."""
        return {
            'name': 'Maintenance Due Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.aircraft',
            'view_mode': 'list,form',
            'domain': [('maintenance_status', '=', 'due_soon')],
        }

    def action_view_cert_expired(self):
        """Open aircraft with expired certificates."""
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
        """Open aircraft with certificates expiring soon."""
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
