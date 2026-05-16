# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Documents fs admin task module.

Purpose:
    Defines classes FsAdminTask for document types, uploaded files, version history, expiry status, previews, and entity shortcuts.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
from odoo import fields, models


class FsAdminTask(models.Model):
    """Extend admin task model with document management.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.admin.task``.
        _inherit: Odoo model(s) extended by this class: ``['fs.admin.task']``.

    Related:
        fs_people and fs_training provide the related business entities whose files are managed here.
    """

    _name = 'fs.admin.task'
    _inherit = ['fs.admin.task']

    document_ids = fields.One2many(
        comodel_name='fs.document',
        inverse_name='admin_task_id',
        string='Documents',
    )
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
    )
    document_reference = fields.Char(
        string='Document Reference',
        compute='_compute_document_info',
        help="Reference from the linked document.",
    )
    document_filename = fields.Char(
        string='Document Filename',
        compute='_compute_document_info',
        help="Filename of the linked document.",
    )

    def _compute_document_count(self):
        """Count documents related to this admin task.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        grouped = self.env['fs.document']._read_group(
            [('admin_task_id', 'in', self.ids)], groupby=['admin_task_id'], aggregates=['__count'])
        count_by_task = {admin_task.id: count for admin_task, count in grouped}
        for record in self:
            record.document_count = count_by_task.get(record.id, 0)

    def _compute_document_info(self):
        """Get document reference and filename from first linked document.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        documents = self.env['fs.document'].search(
            [('admin_task_id', 'in', self.ids)], order='id')
        document_by_task = {}
        for document in documents:
            document_by_task.setdefault(document.admin_task_id.id, document)
        for record in self:
            doc = document_by_task.get(record.id)
            record.document_reference = doc.reference if doc else False
            record.document_filename = doc.filename if doc else False

    def action_view_documents(self):
        """Open list of documents for this admin task.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('admin_task_id', '=', self.id)],
            'context': {
                'default_admin_task_id': self.id,
                'default_training_class_id': self.training_class_id.id,  # type: ignore
            },
        }

    def action_upload_document(self):
        """Open document upload wizard with this admin task pre-selected.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'name': 'Upload Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id,
            'target': 'new',
            'context': {
                'default_admin_task_id': self.id,
                'default_training_class_id': self.training_class_id.id,
            },
        }

    def action_open_document(self):
        """Open the first document for this task in a preview popup.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        doc = self.document_ids[:1]
        if not doc:
            return False

        view_id = self.env.ref('fs_documents.view_fs_document_preview').id
        return {
            'name': 'Document Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'res_id': doc.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }
