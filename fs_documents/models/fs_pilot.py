# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Documents fs pilot module.

Purpose:
    Defines classes FsPilot for document types, uploaded files, version history, expiry status, previews, and entity shortcuts.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
from odoo import api, fields, models


class FsPilot(models.Model):
    """Extend pilot model with document management.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.pilot``.
        _inherit: Odoo model(s) extended by this class: ``['fs.pilot']``.

    Related:
        fs_people and fs_training provide the related business entities whose files are managed here.
    """

    _name = 'fs.pilot'
    _inherit = ['fs.pilot']

    document_ids = fields.One2many(
        comodel_name='fs.document',
        inverse_name='pilot_id',
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
    english_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='English Document',
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
        """Compute the number of documents.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('document_ids', 'document_ids.document_type_id.display_field')
    def _compute_document_shortcuts(self):
        """Find specific document types for quick access buttons based on display_field.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            docs = record.document_ids
            record.medical_document_id = docs.filtered_domain(
                [('document_type_id.display_field', '=', 'medical_expiry')])[:1]
            record.license_document_id = docs.filtered_domain(
                [('document_type_id.display_field', '=', 'license_number')])[:1]
            record.english_document_id = docs.filtered_domain(
                [('document_type_id.display_field', '=', 'english_expiry')])[:1]
            record.security_document_id = docs.filtered_domain(
                [('document_type_id.display_field', '=', 'security_clearance_expiry')])[:1]
            record.insurance_document_id = docs.filtered_domain(
                [('document_type_id.display_field', '=', 'insurance_expiry')])[:1]
            record.id_document_id = docs.filtered_domain(
                [('document_type_id.display_field', '=', 'identification_number')])[:1]

    def action_view_documents(self):
        """View all documents for this pilot.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'name': 'Pilot Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('pilot_id', '=', self.id)],
            'context': {'default_pilot_id': self.id},
        }

    def action_upload_document(self):
        """Open document upload wizard with this pilot pre-selected.

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
            'context': {'default_pilot_id': self.id},
        }

    def action_view_medical_document(self):
        """View medical document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.medical_document_id:
            return self._open_document_preview(self.medical_document_id)

    def action_view_license_document(self):
        """View license document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.license_document_id:
            return self._open_document_preview(self.license_document_id)

    def action_view_english_document(self):
        """View english proficiency document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.english_document_id:
            return self._open_document_preview(self.english_document_id)

    def action_view_security_document(self):
        """View security clearance document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.security_document_id:
            return self._open_document_preview(self.security_document_id)

    def action_view_insurance_document(self):
        """View insurance document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.insurance_document_id:
            return self._open_document_preview(self.insurance_document_id)

    def action_view_id_document(self):
        """View ID document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        if self.id_document_id:
            return self._open_document_preview(self.id_document_id)

    def _open_document_preview(self, document):
        """Open document in preview popup.

        Args:
            document: Value supplied by Odoo or the calling workflow.

        Returns:
            dict: Structured data or an Odoo action dictionary produced by the workflow.
        """
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
