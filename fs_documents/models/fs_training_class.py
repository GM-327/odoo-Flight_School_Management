# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Documents fs training class module.

Purpose:
    Defines classes FsTrainingClass for document types, uploaded files, version history, expiry status, previews, and entity shortcuts.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
from odoo import fields, models


class FsTrainingClass(models.Model):
    """Extend training class model with document management.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.training.class``.
        _inherit: Odoo model(s) extended by this class: ``['fs.training.class']``.

    Related:
        fs_people and fs_training provide the related business entities whose files are managed here.
    """

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
        """Compute the number of documents.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        grouped = self.env['fs.document']._read_group(
            [('training_class_id', 'in', self.ids)], groupby=['training_class_id'], aggregates=['__count'])
        count_by_class = {training_class.id: count for training_class, count in grouped}
        for record in self:
            record.document_count = count_by_class.get(record.id, 0)

    def action_view_documents(self):
        """View all documents for this training class.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
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
        """Open document upload wizard with this training class pre-selected.

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
            'context': {'default_training_class_id': self.id},
        }
