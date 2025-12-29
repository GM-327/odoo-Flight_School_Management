# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsDocumentEntityType(models.Model):
    """Entity types that documents can apply to."""

    _name = 'fs.document.entity.type'
    _description = 'Document Entity Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Technical code (e.g., student, instructor, pilot).",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Entity type code must be unique!',
    )


class FsDocumentType(models.Model):
    """Document type categories for organizing documents."""

    _name = 'fs.document.type'
    _description = 'Document Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Type Name',
        required=True,
        help="Name of the document type (e.g., Medical Certificate, License Copy).",
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Short code for the document type (e.g., MED, LIC).",
    )
    description = fields.Text(
        string='Description',
        help="Optional description of this document type.",
    )
    applies_to_ids = fields.Many2many(
        comodel_name='fs.document.entity.type',
        relation='fs_document_type_entity_rel',
        column1='document_type_id',
        column2='entity_type_id',
        string='Applies To',
        help="Which entity types this document can be associated with.",
    )
    has_expiry = fields.Boolean(
        string='Has Expiry',
        default=True,
        help="Whether documents of this type have an expiry date.",
    )
    expiry_field = fields.Selection(
        selection=[
            ('medical_expiry', 'Medical Expiry'),
            ('license_expiry', 'License Expiry'),
            ('english_expiry', 'English Proficiency Expiry'),
            ('security_clearance_expiry', 'Security Clearance Expiry'),
            ('insurance_expiry', 'Insurance Expiry'),
        ],
        string='Sync Expiry To Field',
        help="Field on target model to sync expiry date TO. "
             "When a document's expiry changes, the related entity's field will be updated.",
    )
    display_field = fields.Selection(
        selection=[
            ('identification_number', 'ID Number'),
            ('medical_expiry', 'Medical Expiry'),
            ('license_expiry', 'License Expiry'),
            ('license_number', 'License Number'),
            ('english_expiry', 'English Proficiency Expiry'),
            ('security_clearance_expiry', 'Security Clearance Expiry'),
            ('insurance_expiry', 'Insurance Expiry'),
        ],
        string='Display Next To Field',
        help="Field on entity form where the document preview icon should appear.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Display order for this document type.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Document type code must be unique!',
    )

