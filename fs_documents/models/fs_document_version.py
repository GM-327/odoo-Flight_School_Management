# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import os
import base64
from odoo import api, fields, models


class FsDocumentVersion(models.Model):
    """Version of a document - stores actual file and metadata.
    
    Each version has its own file, expiry date, issue date, and reference.
    When a new version is uploaded, it becomes the current version.
    """

    _name = 'fs.document.version'
    _description = 'Document Version'
    _order = 'version_number desc'

    document_id = fields.Many2one(
        comodel_name='fs.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True,
    )
    version_number = fields.Integer(
        string='Version',
        required=True,
        default=1,
    )
    
    # === File Data ===
    file = fields.Binary(
        string='File',
        required=True,
        attachment=True,
        help="The document file (image or PDF).",
    )
    filename = fields.Char(
        string='Filename',
        required=True,
    )
    file_type = fields.Selection(
        selection=[
            ('image', 'Image'),
            ('pdf', 'PDF'),
            ('other', 'Other'),
        ],
        string='File Type',
        compute='_compute_file_type',
        store=True,
    )
    file_size = fields.Integer(
        string='File Size (bytes)',
        compute='_compute_file_size',
        store=True,
    )

    # === Version-specific metadata ===
    expiry_date = fields.Date(
        string='Expiry Date',
        help="Expiry date for this version of the document.",
    )
    issue_date = fields.Date(
        string='Issue Date',
        help="When this version of the document was issued.",
    )
    reference = fields.Char(
        string='Reference',
        help="External reference number for this version.",
    )
    notes = fields.Text(
        string='Version Notes',
        help="Notes about this specific version.",
    )

    # === Upload info ===
    upload_date = fields.Datetime(
        string='Upload Date',
        default=fields.Datetime.now,
        required=True,
    )
    uploaded_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Uploaded By',
        default=lambda self: self.env.user,
        required=True,
    )
    is_current = fields.Boolean(
        string='Current Version',
        default=False,
    )

    @api.depends('filename')
    def _compute_file_type(self):
        """Detect file type from extension."""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        pdf_extensions = {'.pdf'}

        for record in self:
            if record.filename:
                ext = os.path.splitext(record.filename.lower())[1]
                if ext in image_extensions:
                    record.file_type = 'image'
                elif ext in pdf_extensions:
                    record.file_type = 'pdf'
                else:
                    record.file_type = 'other'
            else:
                record.file_type = 'other'

    @api.depends('file')
    def _compute_file_size(self):
        """Compute file size from binary data."""
        for record in self:
            if record.file:
                try:
                    record.file_size = len(base64.b64decode(record.file))
                except Exception:
                    record.file_size = 0
            else:
                record.file_size = 0

    @api.model_create_multi
    def create(self, vals_list):
        """Create version, auto-increment version number, and set as current."""
        for vals in vals_list:
            document_id = vals.get('document_id')
            if document_id:
                # Get max version number for this document
                max_version = self.search([
                    ('document_id', '=', document_id),
                ], order='version_number desc', limit=1)
                vals['version_number'] = (max_version.version_number + 1) if max_version else 1

                # Unset current flag on existing versions
                self.search([
                    ('document_id', '=', document_id),
                    ('is_current', '=', True),
                ]).write({'is_current': False})

                # Set this as current
                vals['is_current'] = True

        records = super().create(vals_list)
        
        # Sync expiry to parent document's related entity
        records.document_id.sync_expiry_to_related()  # type: ignore
        
        return records

    def write(self, vals):
        """Update version and sync if expiry changed."""
        result = super().write(vals)
        if 'expiry_date' in vals:
            # If this is the current version, sync to related entity
            self.filtered('is_current').document_id.sync_expiry_to_related()  # type: ignore
        return result

    def action_set_as_current(self):
        """Make this version the current one."""
        self.ensure_one()
        # Unset current on siblings
        self.search([
            ('document_id', '=', self.document_id.id),
            ('is_current', '=', True),
        ]).write({'is_current': False})
        # Set this as current
        self.is_current = True
        # Sync expiry to related entity
        self.document_id.sync_expiry_to_related()  # type: ignore
