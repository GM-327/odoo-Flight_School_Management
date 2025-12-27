# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from datetime import timedelta
from odoo import api, fields, models


class FsDocument(models.Model):
    """Document record - one per document type per entity.
    
    Each document can have multiple versions. The current version
    contains the latest file, expiry date, issue date, and reference.
    """

    _name = 'fs.document'
    _description = 'Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'document_type_id, id'

    # === Core Fields ===
    name = fields.Char(
        string='Document Name',
        compute='_compute_name',
        store=True,
        help="Auto-generated from document type.",
    )
    document_type_id = fields.Many2one(
        comodel_name='fs.document.type',
        string='Document Type',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    document_type_code = fields.Char(
        string='Type Code',
        related='document_type_id.code',
        store=True,
    )

    # === Polymorphic Links (only one should be set) ===
    student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Student',
        ondelete='cascade',
        index=True,
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
        ondelete='cascade',
        index=True,
    )
    pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Pilot',
        ondelete='cascade',
        index=True,
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Training Class',
        ondelete='cascade',
        index=True,
    )
    admin_task_id = fields.Many2one(
        comodel_name='fs.admin.task',
        string='Admin Task',
        ondelete='cascade',
        index=True,
    )

    # === Versioning ===
    version_ids = fields.One2many(
        comodel_name='fs.document.version',
        inverse_name='document_id',
        string='Versions',
    )
    current_version_id = fields.Many2one(
        comodel_name='fs.document.version',
        string='Current Version',
        compute='_compute_current_version',
        store=True,
    )
    version_count = fields.Integer(
        string='Version Count',
        compute='_compute_version_count',
    )

    # === Current Version Data (related from current version) ===
    expiry_date = fields.Date(
        string='Expiry Date',
        related='current_version_id.expiry_date',
        readonly=False,
        store=True,
        tracking=True,
    )
    issue_date = fields.Date(
        string='Issue Date',
        related='current_version_id.issue_date',
        readonly=False,
    )
    reference = fields.Char(
        string='Reference',
        related='current_version_id.reference',
        readonly=False,
    )
    file = fields.Binary(
        string='File',
        related='current_version_id.file',
        readonly=True,
    )
    filename = fields.Char(
        string='Filename',
        related='current_version_id.filename',
        readonly=True,
    )
    file_type = fields.Selection(
        related='current_version_id.file_type',
        readonly=True,
    )

    # === Computed Status ===
    expiry_status = fields.Selection(
        selection=[
            ('valid', 'Valid'),
            ('expiring', 'Expiring Soon'),
            ('expired', 'Expired'),
            ('no_expiry', 'No Expiry'),
        ],
        string='Expiry Status',
        compute='_compute_expiry_status',
        store=True,
    )
    notes = fields.Text(
        string='Notes',
        help="General notes about the document.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # === Constraints ===
    _sql_constraints = [
        ('unique_document_student', 
         'UNIQUE(document_type_id, student_id)', 
         'A document of this type already exists for this student!'),
        ('unique_document_instructor', 
         'UNIQUE(document_type_id, instructor_id)', 
         'A document of this type already exists for this instructor!'),
        ('unique_document_pilot', 
         'UNIQUE(document_type_id, pilot_id)', 
         'A document of this type already exists for this pilot!'),
        ('unique_document_class', 
         'UNIQUE(document_type_id, training_class_id)', 
         'A document of this type already exists for this class!'),
    ]

    @api.depends('document_type_id', 'document_type_id.name')
    def _compute_name(self):
        """Document name = Document Type name."""
        for record in self:
            record.name = record.document_type_id.name if record.document_type_id else ''  # type: ignore

    @api.depends('version_ids', 'version_ids.is_current')
    def _compute_current_version(self):
        """Get the current version of the document."""
        for record in self:
            current = record.version_ids.filtered('is_current')
            record.current_version_id = current[:1]

    def _compute_version_count(self):
        """Count the number of versions."""
        for record in self:
            record.version_count = len(record.version_ids)

    @api.depends('expiry_date', 'document_type_id.has_expiry')
    def _compute_expiry_status(self):
        """Compute expiry status using same logic as related model fields."""
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.document_warning_days', '30'))
        today = fields.Date.context_today(self)
        warning_date = today + timedelta(days=warning_days)

        for record in self:
            if not record.document_type_id.has_expiry or not record.expiry_date:  # type: ignore
                record.expiry_status = 'no_expiry'
            elif record.expiry_date < today:
                record.expiry_status = 'expired'
            elif record.expiry_date <= warning_date:
                record.expiry_status = 'expiring'
            else:
                record.expiry_status = 'valid'

    def write(self, vals):
        """Sync expiry to related entity when changed."""
        result = super().write(vals)
        if 'expiry_date' in vals or 'current_version_id' in vals:
            self.sync_expiry_to_related()
        return result

    def sync_expiry_to_related(self):
        """Sync document expiry date to the related entity's field."""
        for record in self:
            doc_type = record.document_type_id
            if not doc_type.expiry_field or not record.expiry_date:  # type: ignore
                continue

            related_entity = (
                record.student_id or 
                record.instructor_id or 
                record.pilot_id or 
                record.training_class_id
            )
            if related_entity and hasattr(related_entity, doc_type.expiry_field):  # type: ignore
                related_entity.write({doc_type.expiry_field: record.expiry_date})  # type: ignore

    def action_view_versions(self):
        """View version history for this document."""
        self.ensure_one()
        return {
            'name': 'Document Versions',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.version',
            'view_mode': 'list,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id},
        }

    def action_add_version(self):
        """Open wizard to add a new version."""
        self.ensure_one()
        return {
            'name': 'Add New Version',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.version',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id': self.id},
        }

    @api.model
    def get_or_create_for_entity(self, document_type_id, entity_field, entity_id):
        """Find existing document or create new one for entity.
        
        Args:
            document_type_id: ID of fs.document.type
            entity_field: field name like 'student_id', 'instructor_id', etc.
            entity_id: ID of the related entity
            
        Returns:
            fs.document record (existing or newly created)
        """
        domain = [
            ('document_type_id', '=', document_type_id),
            (entity_field, '=', entity_id),
        ]
        existing = self.search(domain, limit=1)
        if existing:
            return existing
        
        return self.create({
            'document_type_id': document_type_id,
            entity_field: entity_id,
        })
