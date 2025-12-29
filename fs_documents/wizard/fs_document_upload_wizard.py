# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from typing import Any
from odoo import api, fields, models
from odoo.exceptions import UserError


class FsDocumentUploadWizard(models.TransientModel):
    """Multi-step wizard for uploading documents.
    
    Flow:
    Step 1: Select entity type, then specific entity, then document type
    Step 2: Upload the file
    Step 3: Enter details (reference, dates) and submit
    """

    _name = 'fs.document.upload.wizard'
    _description = 'Document Upload Wizard'

    document_id = fields.Many2one(
        comodel_name='fs.document',
        string='Updating Document',
        help="If set, we are updating this specific document with a new version.",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        
        # Mapping from context keys to (entity_code, actual_field, xml_id)
        context_keys = [
            ('default_student_id', 'student', 'student_id', 'fs_documents.entity_type_student'),
            ('default_instructor_id', 'instructor', 'instructor_id', 'fs_documents.entity_type_instructor'),
            ('default_pilot_id', 'pilot', 'pilot_id', 'fs_documents.entity_type_pilot'),
            ('default_training_class_id', 'training_class', 'training_class_id', 'fs_documents.entity_type_training_class'),
            ('default_class_type_id', 'class_type', 'class_type_id', 'fs_documents.entity_type_class_type'),
        ]

        # Check for each context key - pre-fill entity type and entity from context
        for ctx_key, code, actual_field, xml_id in context_keys:
            entity_id = self._context.get(ctx_key)
            if entity_id:
                # Get entity type by XML ID first, fallback to search by code
                entity_type = None
                try:
                    entity_type = self.env.ref(xml_id, raise_if_not_found=False)
                except Exception:
                    pass
                
                if not entity_type:
                    entity_type = self.env['fs.document.entity.type'].search([('code', '=', code)], limit=1)
                
                if entity_type:
                    res['entity_type_id'] = entity_type.id
                res[actual_field] = entity_id
                break
                    
        return res

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

    # === Step 1: Entity Type → Entity → Document Type ===
    
    # 1. Entity Type Selection (first)
    entity_type_id = fields.Many2one(
        comodel_name='fs.document.entity.type',
        string='Entity Type',
    )
    entity_type_code = fields.Char(
        related='entity_type_id.code',
        readonly=True,
    )
    
    # 2. Entity Selection (depends on entity type)
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
    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Class Type',
    )
    admin_task_id = fields.Many2one(
        comodel_name='fs.admin.task',
        string='Admin Task',
        help="Optional: Link this document to a specific admin task.",
    )
    admin_task_domain = fields.Binary(
        compute='_compute_admin_task_domain',
    )
    
    # 3. Document Type Selection (filtered by entity type)
    document_type_id = fields.Many2one(
        comodel_name='fs.document.type',
        string='Document Type',
    )
    document_type_code = fields.Char(
        related='document_type_id.code',
        readonly=True,
        string='Document Type Code',
    )
    document_type_domain = fields.Binary(
        compute='_compute_document_type_domain',
        help="Dynamic domain to filter document types by entity type.",
    )
    
    @api.depends('entity_type_id')
    def _compute_document_type_domain(self):
        """Compute domain to filter document types that apply to the selected entity type."""
        for record in self:
            if record.entity_type_id:
                record.document_type_domain = [('applies_to_ids', 'in', [record.entity_type_id.id])]
            else:
                record.document_type_domain = []

    @api.depends('training_class_id')
    def _compute_admin_task_domain(self):
        """Compute domain to filter admin tasks by training class."""
        for record in self:
            if record.training_class_id:
                record.admin_task_domain = [('training_class_id', '=', record.training_class_id.id)]
            else:
                record.admin_task_domain = [('id', '=', False)]  # No tasks available

    @api.onchange('entity_type_id')
    def _onchange_entity_type_id(self):
        """When entity type changes, clear non-matching entity and document type selections."""
        if not self.entity_type_id:
            # Clear all if no entity type
            self.student_id = False
            self.instructor_id = False
            self.pilot_id = False
            self.training_class_id = False
            self.class_type_id = False
            self.admin_task_id = False
            self.document_type_id = False
            return
            
        code = self.entity_type_id.code  # type: ignore
        # Only clear entity fields that don't match the selected entity type
        if code != 'student':
            self.student_id = False
        if code != 'instructor':
            self.instructor_id = False
        if code != 'pilot':
            self.pilot_id = False
        if code != 'training_class':
            self.training_class_id = False
            self.admin_task_id = False  # Also clear admin task
        if code != 'class_type':
            self.class_type_id = False
        # Clear document type since it depends on entity type
        self.document_type_id = False

    @api.onchange('student_id', 'instructor_id', 'pilot_id', 'training_class_id', 'class_type_id')
    def _onchange_entity(self):
        """When entity changes, clear document type to force re-selection."""
        # Only clear document type, not admin_task (which is optional for training class)
        self.document_type_id = False

    @api.onchange('training_class_id')
    def _onchange_training_class_id(self):
        """Reset admin task when training class changes."""
        self.admin_task_id = False

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

    @api.depends('document_id', 'document_type_id', 'student_id', 'instructor_id', 'pilot_id', 'training_class_id', 'admin_task_id', 'class_type_id')
    def _compute_existing_document(self):
        """Check if a document of this type already exists for the entity."""
        for record in self:
            if record.document_id:
                record.existing_document_id = record.document_id
                record.is_new_document = False
                continue
                
            if not record.document_type_id:
                record.existing_document_id = False
                record.is_new_document = True
                continue
                
            domain: list[Any] = [('document_type_id', '=', record.document_type_id.id)]
            if record.student_id:
                domain.append(('student_id', '=', record.student_id.id))
            elif record.instructor_id:
                domain.append(('instructor_id', '=', record.instructor_id.id))
            elif record.pilot_id:
                domain.append(('pilot_id', '=', record.pilot_id.id))
            elif record.training_class_id:
                # If admin task is selected, search by admin_task_id (not training_class_id)
                if record.admin_task_id:
                    domain.append(('admin_task_id', '=', record.admin_task_id.id))
                else:
                    domain.append(('training_class_id', '=', record.training_class_id.id))
                    domain.append(('admin_task_id', '=', False))
            elif record.class_type_id:
                domain.append(('class_type_id', '=', record.class_type_id.id))
            else:
                record.existing_document_id = False
                record.is_new_document = True
                continue

            existing = self.env['fs.document'].search(domain, limit=1)
            record.existing_document_id = existing
            record.is_new_document = not existing

    # === Helper to get selected entity ===
    def _get_selected_entity_info(self):
        """Return (entity_field_name, entity_id) for the selected entity."""
        if self.student_id:
            return ('student_id', self.student_id.id)
        elif self.instructor_id:
            return ('instructor_id', self.instructor_id.id)
        elif self.pilot_id:
            return ('pilot_id', self.pilot_id.id)
        elif self.training_class_id:
            if self.admin_task_id:
                return ('admin_task_id', self.admin_task_id.id)
            return ('training_class_id', self.training_class_id.id)
        elif self.class_type_id:
            return ('class_type_id', self.class_type_id.id)
        return (None, None)

    # === Navigation ===
    def _step_order(self):
        """Return step order."""
        return ['type', 'upload', 'details']

    def _reopen_wizard(self):
        """Reopen wizard with current state."""
        # Use entity-specific view if we have an entity or document_id context
        view_id = False
        if any(self._context.get(k) for k in ['default_student_id', 'default_instructor_id', 'default_pilot_id', 'default_training_class_id', 'default_class_type_id', 'default_document_id']):
             view_id = self.env.ref('fs_documents.view_fs_document_upload_wizard_entity_form').id
             
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'context': dict(self._context),
        }

    def action_next(self):
        """Move to the next step with validation."""
        self.ensure_one()
        steps = self._step_order()
        idx = steps.index(self.state or steps[0])

        # Validate Step 1: Type Selection
        if self.state == 'type':
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
            if code == 'class_type' and not self.class_type_id:
                raise UserError("Please select a class type.")
            
            if not self.document_type_id:
                raise UserError("Please select a document type.")

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
        
        # Prioritize explicit document_id from context/Update File button
        if self.document_id:
            document = self.document_id
        elif self.existing_document_id:
            document = self.existing_document_id
        else:
            entity_field, entity_id = self._get_selected_entity_info()
            if not entity_field:
                raise UserError("Please select a related entity.")
                
            vals: dict[str, Any] = {
                'document_type_id': self.document_type_id.id,
                entity_field: entity_id,
            }
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
