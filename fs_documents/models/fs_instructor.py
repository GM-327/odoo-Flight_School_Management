# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsInstructor(models.Model):
    """Extend instructor model with document management."""

    _name = 'fs.instructor'
    _inherit = ['fs.instructor']

    document_ids = fields.One2many(
        comodel_name='fs.document',
        inverse_name='instructor_id',
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
    id_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='ID Document',
        compute='_compute_document_shortcuts',
    )

    def _compute_document_count(self):
        """Compute the number of documents."""
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('document_ids', 'document_ids.document_type_id.code')
    def _compute_document_shortcuts(self):
        """Find specific document types for quick access buttons."""
        for record in self:
            docs = record.document_ids
            record.medical_document_id = docs.filtered_domain([('document_type_id.code', '=', 'MED')])[:1]
            record.license_document_id = docs.filtered_domain([('document_type_id.code', '=', 'LIC')])[:1]
            record.english_document_id = docs.filtered_domain([('document_type_id.code', '=', 'ENG')])[:1]
            record.id_document_id = docs.filtered_domain([('document_type_id.code', '=', 'ID')])[:1]

    def action_view_documents(self):
        """View all documents for this instructor."""
        self.ensure_one()
        return {
            'name': 'Instructor Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'view_mode': 'list,kanban,form',
            'domain': [('instructor_id', '=', self.id)],
            'context': {'default_instructor_id': self.id},
        }

    def action_view_medical_document(self):
        """View medical document."""
        self.ensure_one()
        if self.medical_document_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'fs.document',
                'res_id': self.medical_document_id.id,
                'view_mode': 'form',
            }

    def action_view_english_document(self):
        """View english proficiency document."""
        self.ensure_one()
        if self.english_document_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'fs.document',
                'res_id': self.english_document_id.id,
                'view_mode': 'form',
            }
