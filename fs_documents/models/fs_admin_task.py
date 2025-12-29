# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsAdminTask(models.Model):
    """Extend admin task model with document management."""

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
        """Count documents related to this admin task."""
        for record in self:
            record.document_count = len(record.document_ids)

    def _compute_document_info(self):
        """Get document reference and filename from first linked document."""
        for record in self:
            doc = record.document_ids[:1]
            record.document_reference = doc.reference if doc else False  # type: ignore
            record.document_filename = doc.filename if doc else False  # type: ignore

    def action_view_documents(self):
        """Open list of documents for this admin task."""
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
        """Open document upload wizard with this admin task pre-selected."""
        self.ensure_one()
        return {
            'name': 'Upload Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id,
            'target': 'new',
            'context': {'default_admin_task_id': self.id},
        }

    def action_open_document(self):
        """Open the first document for this task in a preview popup."""
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
