# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsTrainingClass(models.Model):
    """Extend training class model with document management."""

    _name = 'fs.training.class'
    _inherit = ['fs.training.class']

    document_ids = fields.One2many(
        comodel_name='fs.document',
        inverse_name='training_class_id',
        string='Documents',
    )
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
    )

    def _compute_document_count(self):
        """Compute the number of documents."""
        for record in self:
            record.document_count = len(record.document_ids)

    def action_view_documents(self):
        """View all documents for this training class."""
        self.ensure_one()
        return {
            'name': 'Class Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('training_class_id', '=', self.id)],
            'context': {'default_training_class_id': self.id},
        }

    def action_upload_document(self):
        """Open document upload wizard with this training class pre-selected."""
        self.ensure_one()
        return {
            'name': 'Upload Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id,
            'target': 'new',
            'context': {'default_training_class_id': self.id},
        }
