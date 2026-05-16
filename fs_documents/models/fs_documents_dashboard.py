# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Documents fs documents dashboard module.

Purpose:
    Defines classes FsDocumentsDashboard for document types, uploaded files, version history, expiry status, previews, and entity shortcuts.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
import json

from odoo import api, fields, models


class FsDocumentsDashboard(models.TransientModel):
    """Dashboard for Documents module - provides KPIs and quick actions.

    Uses TransientModel to create temporary records in database.
    Records are automatically cleaned up by Odoo's garbage collection.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.documents.dashboard``.
        _description (str): Human-readable model label, ``Documents Dashboard``.

    Related:
        fs_people and fs_training provide the related business entities whose files are managed here.
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

    @api.model
    def _get_status_counts(self):
        """Return document counts grouped by expiry status."""
        return dict(self.env['fs.document']._read_group(
            [], groupby=['expiry_status'], aggregates=['__count']))

    @api.model
    def _get_entity_counts(self):
        """Return document counts grouped by computed entity type."""
        return dict(self.env['fs.document']._read_group(
            [], groupby=['related_entity_type'], aggregates=['__count']))

    def _compute_summary_kpis(self):
        """Compute top-level summary statistics.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        Document = self.env['fs.document']
        status_counts = self._get_status_counts()
        for record in self:
            total = Document.search_count([])
            expired = status_counts.get('expired', 0)
            record.doc_total = total
            record.doc_health = ((total - expired) / total * 100) if total > 0 else 100.0

    def _compute_document_kpis(self):
        """Compute document status statistics.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        Document = self.env['fs.document']
        status_counts = self._get_status_counts()
        for record in self:
            record.doc_total = Document.search_count([])
            record.doc_expired = status_counts.get('expired', 0)
            record.doc_expiring = status_counts.get('expiring', 0)
            record.doc_valid = status_counts.get('valid', 0)

    def _compute_entity_kpis(self):
        """Compute document counts by entity type.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        entity_counts = self._get_entity_counts()
        for record in self:
            record.doc_students = entity_counts.get('student', 0)
            record.doc_instructors = entity_counts.get('instructor', 0)
            record.doc_pilots = entity_counts.get('pilot', 0)
            record.doc_classes = entity_counts.get('training_class', 0)

    def _compute_doc_graph_data(self):
        """Compute document distribution graph data.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        status_counts = self._get_status_counts()
        entity_counts = self._get_entity_counts()

        # Status distribution
        status_data = [
            {'label': 'Valid', 'value': status_counts.get('valid', 0), 'type': 'future'},
            {'label': 'Expiring', 'value': status_counts.get('expiring', 0), 'type': 'past'},
            {'label': 'Expired', 'value': status_counts.get('expired', 0), 'type': 'past'},
            {'label': 'No Expiry', 'value': status_counts.get('no_expiry', 0), 'type': 'future'},
        ]

        # Entity distribution
        entity_data = [
            {'label': 'Students', 'value': entity_counts.get('student', 0), 'type': 'future'},
            {'label': 'Instructors', 'value': entity_counts.get('instructor', 0), 'type': 'future'},
            {'label': 'Pilots', 'value': entity_counts.get('pilot', 0), 'type': 'future'},
            {'label': 'Classes', 'value': entity_counts.get('training_class', 0), 'type': 'future'},
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
        """Open all documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'All Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
        }

    def action_view_documents_expired(self):
        """Open expired documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Expired Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('expiry_status', '=', 'expired')],
        }

    def action_view_documents_expiring(self):
        """Open expiring documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Expiring Soon',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('expiry_status', '=', 'expiring')],
        }

    def action_view_documents_valid(self):
        """Open valid documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Valid Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('expiry_status', '=', 'valid')],
        }

    def action_view_student_documents(self):
        """Open student documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Student Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('student_id', '!=', False)],
        }

    def action_view_instructor_documents(self):
        """Open instructor documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Instructor Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('instructor_id', '!=', False)],
        }

    def action_view_pilot_documents(self):
        """Open pilot documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Pilot Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('pilot_id', '!=', False)],
        }

    def action_view_class_documents(self):
        """Open training class documents.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        return {
            'name': 'Class Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('training_class_id', '!=', False)],
        }
