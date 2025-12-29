# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsStudent(models.Model):
    """Extend student model with document management."""

    _name = 'fs.student'
    _inherit = ['fs.student']

    document_ids = fields.One2many(
        comodel_name='fs.document',
        inverse_name='student_id',
        string='Documents',
    )
    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
    )

    # Quick access to specific document types
    medical_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='Medical Document',
        compute='_compute_document_shortcuts',
    )
    license_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='License Document',
        compute='_compute_document_shortcuts',
    )
    security_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='Security Document',
        compute='_compute_document_shortcuts',
    )
    insurance_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='Insurance Document',
        compute='_compute_document_shortcuts',
    )
    id_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='ID Document',
        compute='_compute_document_shortcuts',
    )

    def _compute_document_count(self):
        """Compute the number of documents."""
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('document_ids', 'document_ids.document_type_id.display_field')
    def _compute_document_shortcuts(self):
        """Find specific document types for quick access buttons based on display_field."""
        for record in self:
            docs = record.document_ids
            # Find document where display_field matches the entity field
            record.medical_document_id = docs.filtered_domain([('document_type_id.display_field', '=', 'medical_expiry')])[:1]
            record.license_document_id = docs.filtered_domain([('document_type_id.display_field', '=', 'license_expiry')])[:1]
            record.security_document_id = docs.filtered_domain([('document_type_id.display_field', '=', 'security_clearance_expiry')])[:1]
            record.insurance_document_id = docs.filtered_domain([('document_type_id.display_field', '=', 'insurance_expiry')])[:1]
            record.id_document_id = docs.filtered_domain([('document_type_id.display_field', '=', 'identification_number')])[:1]

    def action_view_documents(self):
        """View all documents for this student."""
        self.ensure_one()
        return {
            'name': 'Student Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('student_id', '=', self.id)],
            'context': {'default_student_id': self.id},
        }

    def action_upload_document(self):
        """Open document upload wizard with this student pre-selected."""
        self.ensure_one()
        return {
            'name': 'Upload Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id,
            'target': 'new',
            'context': {'default_student_id': self.id},
        }

    def action_view_medical_document(self):
        """View medical document."""
        self.ensure_one()
        if self.medical_document_id:
            return self._open_document_preview(self.medical_document_id)

    def action_view_license_document(self):
        """View license document."""
        self.ensure_one()
        if self.license_document_id:
            return self._open_document_preview(self.license_document_id)

    def action_view_security_document(self):
        """View security clearance document."""
        self.ensure_one()
        if self.security_document_id:
            return self._open_document_preview(self.security_document_id)

    def action_view_insurance_document(self):
        """View insurance document."""
        self.ensure_one()
        if self.insurance_document_id:
            return self._open_document_preview(self.insurance_document_id)

    def action_view_id_document(self):
        """View ID document."""
        self.ensure_one()
        if self.id_document_id:
            return self._open_document_preview(self.id_document_id)

    def _open_document_preview(self, document):
        """Open document in preview popup."""
        view_id = self.env.ref('fs_documents.view_fs_document_preview').id
        return {
            'name': 'Document Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'res_id': document.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
        }
