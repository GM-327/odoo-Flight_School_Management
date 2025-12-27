# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from typing import Any
from odoo import api, fields, models
from odoo.exceptions import UserError


class FsDocumentUploadWizard(models.TransientModel):
    """Multi-step wizard for uploading documents.
    
    Step 1: Select document type and entity
    Step 2: Upload the file
    Step 3: Enter details (reference, dates) and submit
    """

    _name = 'fs.document.upload.wizard'
    _description = 'Document Upload Wizard'

    # === State Management ===
    state = fields.Selection(
        selection=[
            ('type', '1. Select Type'),
            ('upload', '2. Upload File'),
            ('details', '3. Enter Details'),
        ],
        string='Step',
        default='type',
        required=True,
    )

    # === Step 1: Document Type & Entity ===
    document_type_id = fields.Many2one(
        comodel_name='fs.document.type',
        string='Document Type',
        required=True,
    )
    entity_type_id = fields.Many2one(
        comodel_name='fs.document.entity.type',
        string='Entity Type',
    )
    entity_type_code = fields.Char(
        related='entity_type_id.code',
        readonly=True,
    )
    applies_to_ids = fields.Many2many(
        related='document_type_id.applies_to_ids',
        string='Applies To IDs',
    )
    available_entity_types = fields.Char(
        string='Available Entity Types',
        compute='_compute_available_entity_types',
        help="Comma-separated list of available entity type codes based on document type.",
    )
    # Boolean fields for each entity type availability (for UI visibility)
    can_select_student = fields.Boolean(
        compute='_compute_available_entity_types',
    )
    can_select_instructor = fields.Boolean(
        compute='_compute_available_entity_types',
    )
    can_select_pilot = fields.Boolean(
        compute='_compute_available_entity_types',
    )
    can_select_training_class = fields.Boolean(
        compute='_compute_available_entity_types',
    )
    can_select_admin_task = fields.Boolean(
        compute='_compute_available_entity_types',
    )

    @api.depends('document_type_id', 'document_type_id.applies_to_ids')
    def _compute_available_entity_types(self):
        """Compute which entity types are available based on document type."""
        for record in self:
            doc_type = record.document_type_id
            if doc_type and doc_type.applies_to_ids:  # type: ignore
                codes = doc_type.applies_to_ids.mapped('code')  # type: ignore
            else:
                codes = []
            
            record.available_entity_types = ','.join(codes)
            record.can_select_student = 'student' in codes
            record.can_select_instructor = 'instructor' in codes
            record.can_select_pilot = 'pilot' in codes
            record.can_select_training_class = 'training_class' in codes
            record.can_select_admin_task = 'admin_task' in codes

    @api.onchange('document_type_id')
    def _onchange_document_type_id(self):
        """Reset entity type and entity selections when document type changes."""
        self.entity_type_id = False
        self.student_id = False
        self.instructor_id = False
        self.pilot_id = False
        self.training_class_id = False
        self.admin_task_id = False

    student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Student',
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Instructor',
    )
    pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Pilot',
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Training Class',
    )
    admin_task_id = fields.Many2one(
        comodel_name='fs.admin.task',
        string='Admin Task',
    )

    # === Step 2: File Upload ===
    file = fields.Binary(
        string='File',
        attachment=True,
    )
    filename = fields.Char(
        string='Filename',
    )
    notes = fields.Text(
        string='Notes',
    )

    # === Step 3: Document Details ===
    reference = fields.Char(
        string='Reference',
        help="External reference number (e.g., certificate number).",
    )
    issue_date = fields.Date(
        string='Issue Date',
    )
    expiry_date = fields.Date(
        string='Expiry Date',
    )

    # === Computed for Display ===
    document_type_name = fields.Char(
        related='document_type_id.name',
    )
    has_expiry = fields.Boolean(
        related='document_type_id.has_expiry',
    )
    existing_document_id = fields.Many2one(
        comodel_name='fs.document',
        string='Existing Document',
        compute='_compute_existing_document',
    )
    is_new_document = fields.Boolean(
        string='New Document',
        compute='_compute_existing_document',
    )

    @api.depends('document_type_id', 'student_id', 'instructor_id', 'pilot_id', 'training_class_id', 'admin_task_id')
    def _compute_existing_document(self):
        """Check if a document of this type already exists for the entity."""
        for record in self:
            domain: list[Any] = [('document_type_id', '=', record.document_type_id.id)]
            if record.student_id:
                domain.append(('student_id', '=', record.student_id.id))
            elif record.instructor_id:
                domain.append(('instructor_id', '=', record.instructor_id.id))
            elif record.pilot_id:
                domain.append(('pilot_id', '=', record.pilot_id.id))
            elif record.training_class_id:
                domain.append(('training_class_id', '=', record.training_class_id.id))
            elif record.admin_task_id:
                domain.append(('admin_task_id', '=', record.admin_task_id.id))
            else:
                record.existing_document_id = False
                record.is_new_document = True
                continue

            existing = self.env['fs.document'].search(domain, limit=1)
            record.existing_document_id = existing
            record.is_new_document = not existing

    # === Navigation ===
    def _step_order(self):
        """Return step order."""
        return ['type', 'upload', 'details']

    def _reopen_wizard(self):
        """Reopen wizard with current state."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self._context),
        }

    def action_next(self):
        """Move to the next step with validation."""
        self.ensure_one()
        steps = self._step_order()
        idx = steps.index(self.state or steps[0])

        # Validate Step 1: Type
        if self.state == 'type':
            if not self.document_type_id:
                raise UserError("Please select a document type.")
            if not self.entity_type_id:
                raise UserError("Please select an entity type.")
            
            code = self.entity_type_code
            if code == 'student' and not self.student_id:
                raise UserError("Please select a student.")
            if code == 'instructor' and not self.instructor_id:
                raise UserError("Please select an instructor.")
            if code == 'pilot' and not self.pilot_id:
                raise UserError("Please select a pilot.")
            if code == 'training_class' and not self.training_class_id:
                raise UserError("Please select a training class.")
            if code == 'admin_task' and not self.admin_task_id:
                raise UserError("Please select an admin task.")

        # Validate Step 2: Upload
        if self.state == 'upload':
            if not self.file or not self.filename:
                raise UserError("Please upload a file.")

        if idx < len(steps) - 1:
            self.state = steps[idx + 1]

        return self._reopen_wizard()

    def action_previous(self):
        """Move to previous step."""
        self.ensure_one()
        steps = self._step_order()
        idx = steps.index(self.state or steps[0])
        if idx > 0:
            self.state = steps[idx - 1]
        return self._reopen_wizard()

    def action_submit(self):
        """Create or update document and add new version."""
        self.ensure_one()

        # Validate expiry if required
        if self.has_expiry and not self.expiry_date:
            raise UserError("This document type requires an expiry date.")

        # Find or create document
        Document = self.env['fs.document']
        if self.existing_document_id:
            document = self.existing_document_id
        else:
            vals: dict[str, Any] = {
                'document_type_id': self.document_type_id.id,
            }
            if self.student_id:
                vals['student_id'] = self.student_id.id
            elif self.instructor_id:
                vals['instructor_id'] = self.instructor_id.id
            elif self.pilot_id:
                vals['pilot_id'] = self.pilot_id.id
            elif self.training_class_id:
                vals['training_class_id'] = self.training_class_id.id
            elif self.admin_task_id:
                vals['admin_task_id'] = self.admin_task_id.id
            else:
                raise UserError("Please select a related entity.")

            document = Document.create(vals)

        # Create new version
        self.env['fs.document.version'].create({
            'document_id': document.id,
            'file': self.file,
            'filename': self.filename,
            'reference': self.reference,
            'issue_date': self.issue_date,
            'expiry_date': self.expiry_date,
            'notes': self.notes,
        })

        # Open the document
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fs.document',
            'res_id': document.id,
            'view_mode': 'form',
            'target': 'current',
        }
