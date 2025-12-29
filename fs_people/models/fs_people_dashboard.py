# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import json
from odoo import api, fields, models


class FsPeopleDashboard(models.TransientModel):
    """Dashboard for People module - provides KPIs and quick actions.
    
    Uses TransientModel to create temporary records in database.
    Records are automatically cleaned up by Odoo's garbage collection.
    """

    _name = 'fs.people.dashboard'
    _description = 'People Dashboard'

    name = fields.Char(string='Name', default='People Dashboard')

    # === Graph Data ===
    student_distribution = fields.Text(
        string='Student Distribution Graph',
        compute='_compute_student_graph_data',
    )
    instructor_distribution = fields.Text(
        string='Instructor Distribution Graph',
        compute='_compute_instructor_graph_data',
    )

    # === Summary KPIs ===
    personnel_total = fields.Integer(
        string='Total Personnel',
        compute='_compute_summary_kpis',
    )
    compliance_health = fields.Float(
        string='Compliance Health (%)',
        compute='_compute_summary_kpis',
    )

    # === Instructor KPIs ===
    instructor_total = fields.Integer(
        string='Total Instructors',
        compute='_compute_instructor_kpis',
    )
    instructor_expired = fields.Integer(
        string='Instructors Expired',
        compute='_compute_instructor_kpis',
    )
    instructor_expiring = fields.Integer(
        string='Instructors Expiring',
        compute='_compute_instructor_kpis',
    )

    # === Student KPIs ===
    student_total = fields.Integer(
        string='Total Students',
        compute='_compute_student_kpis',
    )
    student_expired = fields.Integer(
        string='Students Expired',
        compute='_compute_student_kpis',
    )
    student_expiring = fields.Integer(
        string='Students Expiring',
        compute='_compute_student_kpis',
    )

    # === Pilot KPIs ===
    pilot_total = fields.Integer(
        string='Total Pilots',
        compute='_compute_pilot_kpis',
    )
    pilot_expired = fields.Integer(
        string='Pilots Expired',
        compute='_compute_pilot_kpis',
    )
    pilot_expiring = fields.Integer(
        string='Pilots Expiring',
        compute='_compute_pilot_kpis',
    )

    def _compute_instructor_kpis(self):
        """Compute instructor statistics."""
        Instructor = self.env['fs.instructor']
        for record in self:
            record.instructor_total = Instructor.search_count([])
            # Expired: medical or any qualification expired
            record.instructor_expired = Instructor.search_count([
                '|',
                ('medical_status', '=', 'expired'),
                ('has_expired_qualification', '=', True),
            ])
            # Expiring: medical or english expiring (not expired)
            record.instructor_expiring = Instructor.search_count([
                '|',
                ('medical_status', '=', 'expiring'),
                ('english_status', '=', 'expiring'),
            ])

    def _compute_student_kpis(self):
        """Compute student statistics."""
        Student = self.env['fs.student']
        for record in self:
            record.student_total = Student.search_count([])
            # Any status expired
            record.student_expired = Student.search_count([
                ('has_expired_status', '=', True),
            ])
            # Any status expiring soon
            record.student_expiring = Student.search_count([
                '|', '|', '|',
                ('license_expiry_status', '=', 'expiring'),
                ('medical_status', '=', 'expiring'),
                ('security_clearance_status', '=', 'expiring'),
                ('insurance_status', '=', 'expiring'),
            ])

    def _compute_pilot_kpis(self):
        """Compute pilot statistics."""
        Pilot = self.env['fs.pilot']
        for record in self:
            record.pilot_total = Pilot.search_count([])
            # Any qualification or status expired
            record.pilot_expired = Pilot.search_count([
                ('has_expired_qualification', '=', True),
            ])
            # Any status expiring
            record.pilot_expiring = Pilot.search_count([
                '|', '|', '|',
                ('medical_status', '=', 'expiring'),
                ('english_status', '=', 'expiring'),
                ('security_clearance_status', '=', 'expiring'),
                ('insurance_status', '=', 'expiring'),
            ])

    def _compute_summary_kpis(self):
        """Compute top-level summary statistics."""
        Instructor = self.env['fs.instructor']
        Student = self.env['fs.student']
        Pilot = self.env['fs.pilot']
        for record in self:
            i_total = Instructor.search_count([])
            s_total = Student.search_count([])
            p_total = Pilot.search_count([])
            i_expired = Instructor.search_count([
                '|', ('medical_status', '=', 'expired'), ('has_expired_qualification', '=', True)
            ])
            s_expired = Student.search_count([('has_expired_status', '=', True)])
            p_expired = Pilot.search_count([('has_expired_qualification', '=', True)])
            total = i_total + s_total + p_total
            expired = i_expired + s_expired + p_expired
            record.personnel_total = total
            record.compliance_health = ((total - expired) / total * 100) if total > 0 else 100.0

    def _compute_student_graph_data(self):
        """Compute student distribution graph data."""
        Student = self.env['fs.student']
        # Distribution by license type
        data = []
        license_types = self.env['fs.license.type'].search([])
        for lt in license_types:
            count = Student.search_count([('license_id', '=', lt.id)])
            if count > 0:
                data.append({
                    'label': getattr(lt, 'name', 'Unknown'),
                    'value': count,
                    'type': 'future'
                })
        
        # Add a bar for those without license type if any
        none_count = Student.search_count([('license_id', '=', False)])
        if none_count > 0:
            data.append({
                'label': 'None',
                'value': none_count,
                'type': 'past'
            })

        for record in self:
            record.student_distribution = json.dumps([{
                'values': data,
                'key': 'Students by License Type',
            }])

    def _compute_instructor_graph_data(self):
        """Compute instructor distribution graph data."""
        Instructor = self.env['fs.instructor']
        # Distribution by medical status
        data = [
            {'label': 'Valid', 'value': Instructor.search_count([('medical_status', '=', 'valid')]), 'type': 'future'},
            {'label': 'Expiring', 'value': Instructor.search_count([('medical_status', '=', 'expiring')]), 'type': 'past'},
            {'label': 'Expired', 'value': Instructor.search_count([('medical_status', '=', 'expired')]), 'type': 'past'},
        ]
        for record in self:
            record.instructor_distribution = json.dumps([{
                'values': data,
                'key': 'Instructors Medical Status',
            }])

    # === Action Methods ===
    def action_view_instructors(self):
        """Open instructors list."""
        return {
            'name': 'Instructors',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.instructor',
            'view_mode': 'list,kanban,form',
            'context': {'search_default_group_department': 1},
        }

    def action_view_instructors_expired(self):
        """Open instructors with expired status."""
        return {
            'name': 'Instructors - Expired Status',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.instructor',
            'view_mode': 'list,form',
            'domain': [
                '|',
                ('medical_status', '=', 'expired'),
                ('has_expired_qualification', '=', True),
            ],
        }

    def action_view_instructors_expiring(self):
        """Open instructors with expiring status."""
        return {
            'name': 'Instructors - Expiring Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.instructor',
            'view_mode': 'list,form',
            'domain': [
                '|',
                ('medical_status', '=', 'expiring'),
                ('english_status', '=', 'expiring'),
            ],
        }

    def action_view_students(self):
        """Open students list."""
        return {
            'name': 'Students',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student',
            'view_mode': 'list,kanban,form',
        }

    def action_view_students_expired(self):
        """Open students with expired status."""
        return {
            'name': 'Students - Expired Status',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student',
            'view_mode': 'list,form',
            'domain': [('has_expired_status', '=', True)],
        }

    def action_view_students_expiring(self):
        """Open students with expiring status."""
        return {
            'name': 'Students - Expiring Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.student',
            'view_mode': 'list,form',
            'domain': [
                '|', '|', '|',
                ('license_expiry_status', '=', 'expiring'),
                ('medical_status', '=', 'expiring'),
                ('security_clearance_status', '=', 'expiring'),
                ('insurance_status', '=', 'expiring'),
            ],
        }

    def action_view_pilots(self):
        """Open pilots list."""
        return {
            'name': 'Pilots',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.pilot',
            'view_mode': 'list,kanban,form',
        }

    def action_view_pilots_expired(self):
        """Open pilots with expired status."""
        return {
            'name': 'Pilots - Expired Status',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.pilot',
            'view_mode': 'list,form',
            'domain': [('has_expired_qualification', '=', True)],
        }

    def action_view_pilots_expiring(self):
        """Open pilots with expiring status."""
        return {
            'name': 'Pilots - Expiring Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.pilot',
            'view_mode': 'list,form',
            'domain': [
                '|', '|', '|',
                ('medical_status', '=', 'expiring'),
                ('english_status', '=', 'expiring'),
                ('security_clearance_status', '=', 'expiring'),
                ('insurance_status', '=', 'expiring'),
            ],
        }
