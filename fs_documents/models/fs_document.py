# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Documents fs document module.

Purpose:
    Defines classes FsDocument for document types, uploaded files, version history, expiry status, previews, and entity shortcuts.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: web, fs_core, fs_people, fs_training.
    fs_people and fs_training provide the related business entities whose files are managed here.
"""
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class FsDocument(models.Model):
    """Document record - one per document type per entity.

    Each document can have multiple versions. The current version
    contains the latest file, expiry date, issue date, and reference.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.document``.
        _inherit: Odoo model(s) extended by this class: ``['mail.thread', 'mail.activity.mixin']``.
        _description (str): Human-readable model label, ``Document``.

    Related:
        fs_people and fs_training provide the related business entities whose files are managed here.
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
    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Class Type',
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

    # === Computed Entity Info for Views ===
    related_entity_name = fields.Char(
        string='Belongs To',
        compute='_compute_related_entity_info',
        store=True,
    )
    related_entity_type = fields.Selection(
        selection=[
            ('student', 'Student'),
            ('instructor', 'Instructor'),
            ('pilot', 'Pilot'),
            ('training_class', 'Training Class'),
            ('admin_task', 'Admin Task'),
            ('class_type', 'Class Type'),
        ],
        string='Entity Type',
        compute='_compute_related_entity_info',
        store=True,
    )

    @api.depends('student_id', 'instructor_id', 'pilot_id', 'training_class_id', 'admin_task_id', 'class_type_id')
    def _compute_related_entity_info(self):
        """Compute the name and type of the related entity for unified display.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            name = False
            etype = False

            if record.student_id:
                name = record.student_id.display_name
                etype = 'student'
            elif record.instructor_id:
                name = record.instructor_id.display_name
                etype = 'instructor'
            elif record.pilot_id:
                name = record.pilot_id.display_name
                etype = 'pilot'
            elif record.training_class_id:
                name = record.training_class_id.display_name
                etype = 'training_class'
            elif record.admin_task_id:
                name = record.admin_task_id.display_name
                etype = 'admin_task'
            elif record.class_type_id:
                name = record.class_type_id.display_name
                etype = 'class_type'

            record.related_entity_name = name
            record.related_entity_type = etype

    # === Constraints ===
    _unique_document_student = models.Constraint(
        'UNIQUE(document_type_id, student_id)',
        'A document of this type already exists for this student!',
    )
    _unique_document_instructor = models.Constraint(
        'UNIQUE(document_type_id, instructor_id)',
        'A document of this type already exists for this instructor!',
    )
    _unique_document_pilot = models.Constraint(
        'UNIQUE(document_type_id, pilot_id)',
        'A document of this type already exists for this pilot!',
    )
    _unique_document_class = models.Constraint(
        'UNIQUE(document_type_id, training_class_id)',
        'A document of this type already exists for this class!',
    )
    _unique_document_class_type = models.Constraint(
        'UNIQUE(document_type_id, class_type_id)',
        'A document of this type already exists for this class type!',
    )
    _unique_document_admin_task = models.Constraint(
        'UNIQUE(document_type_id, admin_task_id)',
        'A document of this type already exists for this admin task!',
    )

    @api.constrains(
        'document_type_id', 'student_id', 'instructor_id', 'pilot_id',
        'training_class_id', 'admin_task_id', 'class_type_id'
    )
    def _check_single_related_entity(self):
        """Require each document to belong to exactly one supported entity.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            ValidationError: If record data violates a model constraint.
        """
        # The document model uses explicit nullable Many2one fields instead
        # of a generic reference so each target can have its own access rules
        # and unique constraint. Exactly one of these fields must be populated.
        entity_fields = (
            'student_id', 'instructor_id', 'pilot_id',
            'training_class_id', 'admin_task_id', 'class_type_id',
        )
        for record in self:
            linked_count = sum(1 for field_name in entity_fields if record[field_name])
            if linked_count != 1:
                raise ValidationError(
                    self.env._("A document must be linked to exactly one related entity.")
                )

    @api.depends('document_type_id', 'document_type_id.name', 'admin_task_id', 'admin_task_id.name')
    def _compute_name(self):
        """Document name = Admin Task name (for admin docs) or Document Type name.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            name = ''
            if record.admin_task_id:
                name = record.admin_task_id.display_name
            elif record.document_type_id:
                name = record.document_type_id.display_name
            record.name = name or 'New Document'

    @api.depends('version_ids', 'version_ids.is_current')
    def _compute_current_version(self):
        """Get the current version of the document.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            current = record.version_ids.filtered('is_current')
            record.current_version_id = current[:1]

    def _compute_version_count(self):
        """Count the number of versions.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.version_count = len(record.version_ids)

    @api.depends('expiry_date', 'document_type_id.has_expiry')
    def _compute_expiry_status(self):
        """Compute expiry status using same logic as related model fields.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        warning_days = int(self.env['ir.config_parameter'].sudo().get_param(  # type: ignore
            'flight_school.document_warning_days', '30'))
        # Use the user's context date so expiry warnings respect timezone and
        # company context in scheduled actions and interactive sessions.
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
        """Sync expiry to related entity when changed.

        Args:
            vals: Field values to write or create, following Odoo ORM conventions.

        Returns:
            bool: True when Odoo successfully writes the requested values.
        """
        result = super().write(vals)
        if 'expiry_date' in vals or 'current_version_id' in vals:
            self.sync_expiry_to_related()
        return result

    def sync_expiry_to_related(self):
        """Sync document expiry date to the related entity's field.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
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
        """View version history for this document.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
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
        """Open the upload wizard to add a new version.

        Prefills the wizard with current document data and skips to Step 2.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'name': 'Update Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
                'default_state': 'upload',  # Start at Step 2
            }
        }

    @api.model
    def get_or_create_for_entity(self, document_type_id, entity_field, entity_id):
        """Find existing document or create new one for entity.

        Args:
            document_type_id: Value supplied by Odoo or the calling workflow.
            entity_field: Value supplied by Odoo or the calling workflow.
            entity_id: Value supplied by Odoo or the calling workflow.

        Returns:
            Any: Value required by the Odoo ORM, action system, or calling workflow.
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

    def action_open_upload_wizard(self):
        """Open the upload wizard, using entity-specific view if context has an entity.

        Called from the Upload Document button in list/kanban views.
        Detects if we're coming from an entity-filtered view and opens the appropriate wizard.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        # Check for entity context keys
        context_keys = [
            'default_student_id',
            'default_instructor_id',
            'default_pilot_id',
            'default_training_class_id',
            'default_class_type_id',
            'default_admin_task_id',
        ]

        has_entity = any(self.env.context.get(key) for key in context_keys)

        if has_entity:
            # Use entity-specific wizard view
            view_id = self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id
        else:
            # Use generic wizard view
            view_id = self.env.ref('fs_documents.view_fs_document_upload_wizard_form').id

        return {
            'name': 'Upload Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document.upload.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': dict(self.env.context),
        }

    def action_open_preview(self):
        """Open a popup preview of the current version.

        Returns:
            dict | None: Odoo action dictionary, or None when no action is needed.
        """
        self.ensure_one()
        return {
            'name': 'Document Preview',
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('fs_documents.view_fs_document_preview').id,
            'target': 'new',
            'context': {'dialog_size': 'extra-large'},
        }
