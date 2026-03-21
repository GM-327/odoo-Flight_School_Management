# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import json
from odoo import api, fields, models


class FsDocumentsDashboard(models.TransientModel):
    """Dashboard for Documents module - provides KPIs and quick actions.
    
    Uses TransientModel to create temporary records in database.
    Records are automatically cleaned up by Odoo's garbage collection.
    """

    _name = 'fs.documents.dashboard'
    _description = 'Documents Dashboard'

    name = fields.Char(string='Name', default='Documents Dashboard')

    # === Graph Data ===
    status_distribution = fields.Text(
        string='Status Distribution Graph',
        compute='_compute_doc_graph_data',
    )
    entity_distribution = fields.Text(
        string='Entity Distribution Graph',
        compute='_compute_doc_graph_data',
    )

    # === Document Status KPIs ===
    doc_total = fields.Integer(
        string='Total Documents',
        compute='_compute_summary_kpis',
    )
    doc_health = fields.Float(
        string='Document Health (%)',
        compute='_compute_summary_kpis',
    )
    doc_expired = fields.Integer(
        string='Expired Documents',
        compute='_compute_document_kpis',
    )
    doc_expiring = fields.Integer(
        string='Expiring Soon',
        compute='_compute_document_kpis',
    )
    doc_valid = fields.Integer(
        string='Valid Documents',
        compute='_compute_document_kpis',
    )

    # === Documents by Entity KPIs ===
    doc_students = fields.Integer(
        string='Student Documents',
        compute='_compute_entity_kpis',
    )
    doc_instructors = fields.Integer(
        string='Instructor Documents',
        compute='_compute_entity_kpis',
    )
    doc_pilots = fields.Integer(
        string='Pilot Documents',
        compute='_compute_entity_kpis',
    )
    doc_classes = fields.Integer(
        string='Class Documents',
        compute='_compute_entity_kpis',
    )

    def _compute_summary_kpis(self):
        """Compute top-level summary statistics."""
        Document = self.env['fs.document']
        for record in self:
            total = Document.search_count([])
            expired = Document.search_count([('expiry_status', '=', 'expired')])
            record.doc_total = total
            record.doc_health = ((total - expired) / total * 100) if total > 0 else 100.0

    def _compute_document_kpis(self):
        """Compute document status statistics."""
        Document = self.env['fs.document']
        for record in self:
            record.doc_total = Document.search_count([])
            record.doc_expired = Document.search_count([
                ('expiry_status', '=', 'expired'),
            ])
            record.doc_expiring = Document.search_count([
                ('expiry_status', '=', 'expiring'),
            ])
            record.doc_valid = Document.search_count([
                ('expiry_status', '=', 'valid'),
            ])

    def _compute_entity_kpis(self):
        """Compute document counts by entity type."""
        Document = self.env['fs.document']
        for record in self:
            record.doc_students = Document.search_count([
                ('student_id', '!=', False),
            ])
            record.doc_instructors = Document.search_count([
                ('instructor_id', '!=', False),
            ])
            record.doc_pilots = Document.search_count([
                ('pilot_id', '!=', False),
            ])
            record.doc_classes = Document.search_count([
                ('training_class_id', '!=', False),
            ])

    def _compute_doc_graph_data(self):
        """Compute document distribution graph data."""
        Doc = self.env['fs.document']
        
        # Status distribution
        status_data = [
            {'label': 'Valid', 'value': Doc.search_count([('expiry_status', '=', 'valid')]), 'type': 'future'},
            {'label': 'Expiring', 'value': Doc.search_count([('expiry_status', '=', 'expiring')]), 'type': 'past'},
            {'label': 'Expired', 'value': Doc.search_count([('expiry_status', '=', 'expired')]), 'type': 'past'},
            {'label': 'No Expiry', 'value': Doc.search_count([('expiry_status', '=', 'no_expiry')]), 'type': 'future'},
        ]
        
        # Entity distribution
        entity_data = [
            {'label': 'Students', 'value': Doc.search_count([('student_id', '!=', False)]), 'type': 'future'},
            {'label': 'Instructors', 'value': Doc.search_count([('instructor_id', '!=', False)]), 'type': 'future'},
            {'label': 'Pilots', 'value': Doc.search_count([('pilot_id', '!=', False)]), 'type': 'future'},
            {'label': 'Classes', 'value': Doc.search_count([('training_class_id', '!=', False)]), 'type': 'future'},
        ]
        
        for record in self:
            record.status_distribution = json.dumps([{
                'values': status_data,
                'key': 'Documents by Status',
            }])
            record.entity_distribution = json.dumps([{
                'values': entity_data,
                'key': 'Documents by Entity',
            }])

    # === Action Methods ===
    def action_view_documents(self):
        """Open all documents."""
        return {
            'name': 'All Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
        }

    def action_view_documents_expired(self):
        """Open expired documents."""
        return {
            'name': 'Expired Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('expiry_status', '=', 'expired')],
        }

    def action_view_documents_expiring(self):
        """Open expiring documents."""
        return {
            'name': 'Expiring Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('expiry_status', '=', 'expiring')],
        }

    def action_view_documents_valid(self):
        """Open valid documents."""
        return {
            'name': 'Valid Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('expiry_status', '=', 'valid')],
        }

    def action_view_student_documents(self):
        """Open student documents."""
        return {
            'name': 'Student Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('student_id', '!=', False)],
        }

    def action_view_instructor_documents(self):
        """Open instructor documents."""
        return {
            'name': 'Instructor Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('instructor_id', '!=', False)],
        }

    def action_view_pilot_documents(self):
        """Open pilot documents."""
        return {
            'name': 'Pilot Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('pilot_id', '!=', False)],
        }

    def action_view_class_documents(self):
        """Open training class documents."""
        return {
            'name': 'Class Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('training_class_id', '!=', False)],
        }
