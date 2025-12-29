# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsClassType(models.Model):
    """Extend class type model with document management."""

    _name = 'fs.class.type'
    _inherit = ['fs.class.type']

    reference_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='IP Document',
        help="Reference document (Instruction Permanente) for this class type.",
        domain="[('document_type_id.code', '=', 'IP'), ('class_type_id', '=', id)]",
    )
    ip_document_reference = fields.Char(
        string='IP Reference',
        related='reference_document_id.reference',
        readonly=True,
    )
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
    )

    def _compute_document_count(self):
        """Count documents related to this class type."""
        for record in self:
            record.document_count = self.env['fs.document'].search_count([
                ('class_type_id', '=', record.id)
            ])

    def action_view_documents(self):
        """Open list of documents for this class type."""
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'kanban,list,form',
            'domain': [('class_type_id', '=', self.id)],
            'context': {'default_class_type_id': self.id},
        }

    def action_upload_document(self):
        """Open document upload wizard with this class type pre-selected."""
        self.ensure_one()
        return {
            'name': 'Upload Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id,
            'target': 'new',
            'context': {'default_class_type_id': self.id},
        }

    def action_open_ip_document(self):
        """Open the IP document in a preview popup."""
        self.ensure_one()
        if not self.reference_document_id:
            return False
        
        view_id = self.env.ref('fs_documents.view_fs_document_preview').id
        return {
            'name': 'IP Document Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'res_id': self.reference_document_id.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }
