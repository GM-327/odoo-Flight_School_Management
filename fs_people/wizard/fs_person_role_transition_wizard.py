# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Role transition wizard for Flight School People."""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsPersonRoleTransitionWizard(models.TransientModel):
    """Execute Student -> Pilot and Pilot -> Instructor transfers atomically."""

    _name = 'fs.person.role.transition.wizard'
    _description = 'Person Role Transition Wizard'

    COMMON_COPY_FIELDS = (
        'image', 'name', 'identification_number', 'gender', 'birth_date',
        'nationality_id', 'phone', 'address', 'is_military', 'rank_id',
        'service_number', 'medical_class_id', 'medical_expiry', 'user_id',
        'notes',
    )
    STUDENT_TO_PILOT_COPY_FIELDS = (
        'security_clearance_expiry', 'insurance_expiry', 'advance_payment',
        'currency_id', 'total_flight_hours', 'total_sim_hours', 'solo_hours',
        'last_flight_date',
    )
    PILOT_TO_INSTRUCTOR_COPY_FIELDS = (
        'department_id', 'callsign', 'license_id', 'license_number',
        'license_issue_date', 'english_level_id', 'english_expiry',
        'total_flight_hours', 'total_sim_hours', 'solo_hours',
        'last_flight_date',
    )
    SOURCE_ROLE_LABELS = {
        'fs.student': 'Student',
        'fs.pilot': 'Pilot',
    }
    TARGET_ENTITY_FIELDS = {
        'fs.student': 'student_id',
        'fs.pilot': 'pilot_id',
        'fs.instructor': 'instructor_id',
    }

    source_model = fields.Selection(
        selection=[('fs.student', 'Student'), ('fs.pilot', 'Pilot')],
        string='Source Model',
        required=True,
        readonly=True,
    )
    source_res_id = fields.Integer(
        string='Source Record ID',
        required=True,
        readonly=True,
    )
    source_display_name = fields.Char(
        string='Source Person',
        compute='_compute_source_display_name',
    )
    transition_type = fields.Selection(
        selection=[
            ('student_to_pilot', 'Student -> Pilot'),
            ('pilot_to_instructor', 'Pilot -> Instructor'),
        ],
        string='Transition Type',
        required=True,
        readonly=True,
    )
    transition_date = fields.Date(
        string='Transition Date',
        default=fields.Date.context_today,
        required=True,
    )
    reason = fields.Text(
        string='Reason',
    )
    copy_documents = fields.Boolean(
        string='Copy Applicable Documents',
        default=True,
        help='Copy current document files to the target role when the document type applies to that role.',
    )
    copy_qualifications = fields.Boolean(
        string='Copy Qualifications',
        default=True,
        help='Copy pilot qualifications to the new instructor role.',
    )
    reassign_future_assignments = fields.Boolean(
        string='Reassign Future Assignments',
        help='Move future scheduled/planned assignments from the source pilot to the new instructor.',
    )

    target_license_id = fields.Many2one(
        comodel_name='fs.license.type',
        string='Target License Type',
        domain=[('is_student_related', '=', False)],
    )
    target_license_number = fields.Char(
        string='Target License Number',
    )
    target_license_issue_date = fields.Date(
        string='Target License Issue Date',
    )
    target_callsign = fields.Char(
        string='Target Callsign',
    )
    target_department_id = fields.Many2one(
        comodel_name='fs.department',
        string='Target Department',
    )
    target_english_level_id = fields.Many2one(
        comodel_name='fs.english.level',
        string='Target English Level',
    )
    target_english_expiry = fields.Date(
        string='Target English Expiry',
    )
    target_total_instruction_hours = fields.Float(
        string='Initial Instruction Hours',
        help='Initial instruction hours for the new instructor role.',
    )

    @api.model
    def default_get(self, fields_list):
        """Populate wizard defaults from the source role.

        Args:
            fields_list: Fields requested by the framework.

        Returns:
            dict: Default values.
        """
        values = super().default_get(fields_list)
        source_model = values.get('source_model') or self.env.context.get('default_source_model')
        source_res_id = values.get('source_res_id') or self.env.context.get('default_source_res_id')
        transition_type = values.get('transition_type') or self.env.context.get('default_transition_type')
        if not source_model or not source_res_id:
            return values

        source = self.env[source_model].browse(source_res_id).exists()
        if not source:
            return values

        values.update({
            'source_model': source_model,
            'source_res_id': source.id,
            'transition_type': transition_type,
            'target_callsign': getattr(source, 'callsign', False),
            'target_department_id': getattr(source, 'department_id', False).id if getattr(source, 'department_id', False) else False,
        })
        if transition_type == 'pilot_to_instructor':
            values.update({
                'target_license_id': source.license_id.id if source.license_id else False,
                'target_license_number': source.license_number,
                'target_license_issue_date': source.license_issue_date,
                'target_english_level_id': source.english_level_id.id if source.english_level_id else False,
                'target_english_expiry': source.english_expiry,
            })
        return values

    @api.depends('source_model', 'source_res_id')
    def _compute_source_display_name(self):
        """Compute source role display name.

        Returns:
            None: Updates Odoo records in place.
        """
        for record in self:
            source = record._get_source_record()
            role_label = record.SOURCE_ROLE_LABELS.get(record.source_model, record.source_model or '')
            record.source_display_name = '%s: %s' % (
                role_label,
                source.display_name if source else self.env._('Unknown'),
            )

    def _get_source_record(self):
        """Return the selected source role record.

        Returns:
            models.Model | bool: Source role record or False.
        """
        self.ensure_one()
        if not self.source_model or not self.source_res_id:
            return False
        return self.env[self.source_model].with_context(active_test=False).browse(self.source_res_id).exists()

    def _copy_field_values(self, source, target_model_name, field_names):
        """Copy compatible fields from a source role to a target role value dict.

        Args:
            source: Source role record.
            target_model_name: Target Odoo model name.
            field_names: Field names to copy.

        Returns:
            dict: Values ready for ``create``.
        """
        target_fields = self.env[target_model_name]._fields
        values = {}
        for field_name in field_names:
            if field_name not in source._fields or field_name not in target_fields:
                continue
            target_field = target_fields[field_name]
            field_value = source[field_name]
            if target_field.type == 'many2one':
                values[field_name] = field_value.id if field_value else False
            elif target_field.type == 'many2many':
                values[field_name] = [(6, 0, field_value.ids)]
            else:
                values[field_name] = field_value
        return values

    def _validate_source_role(self, source, expected_model):
        """Validate common source role invariants.

        Args:
            source: Source role record.
            expected_model: Expected Odoo model name.

        Raises:
            UserError: If the source role cannot be transferred.
        """
        if not source or source._name != expected_model:
            raise UserError(self.env._('The selected source role is not valid for this transition.'))
        if source.role_state != 'current' or not source.active:
            raise UserError(self.env._('Only active current roles can be transferred.'))
        if source.transition_out_id and source.transition_out_id.state == 'done':
            raise UserError(self.env._('This role has already been transferred.'))
        source._ensure_person_identity()
        if source.role_start_date and self.transition_date < source.role_start_date:
            raise UserError(self.env._('Transition date cannot be before the source role start date.'))

    def _validate_target_license(self):
        """Validate license fields required for target pilot/instructor roles.

        Raises:
            UserError: If required target license data is missing or invalid.
        """
        if not self.target_license_id or not self.target_license_number:
            raise UserError(self.env._('Target license type and license number are required.'))
        if self.target_license_id.is_student_related:
            raise UserError(self.env._('Target license type must be a pilot/instructor license type.'))

    def _validate_student_to_pilot(self, student):
        """Validate a Student -> Pilot transfer.

        Args:
            student: Source ``fs.student`` record.

        Raises:
            UserError: If transfer would break training history or role integrity.
        """
        self._validate_source_role(student, 'fs.student')
        self._validate_target_license()
        identity = student.person_identity_id
        current_pilot = self.env['fs.pilot'].with_context(active_test=False).search([
            ('person_identity_id', '=', identity.id),
            ('role_state', '=', 'current'),
            ('active', '=', True),
        ], limit=1)
        current_instructor = self.env['fs.instructor'].with_context(active_test=False).search([
            ('person_identity_id', '=', identity.id),
            ('role_state', '=', 'current'),
            ('active', '=', True),
        ], limit=1)
        if current_pilot or current_instructor:
            raise UserError(self.env._('This identity already has a current pilot or instructor role.'))

        Enrollment = self.env.get('fs.student.enrollment')
        if Enrollment is not None:
            open_enrollment = Enrollment.search([
                ('student_id', '=', student.id),
                ('status', 'in', ['enrolled', 'active']),
            ], limit=1)
            if open_enrollment:
                raise UserError(self.env._(
                    'Student %(student)s still has an open enrollment in %(class_name)s. '
                    'Graduate, drop, or cancel the enrollment first so all hours, syllabus completion, '
                    'and progression details remain historical on the student enrollment.'
                ) % {
                    'student': student.display_name,
                    'class_name': open_enrollment.training_class_id.display_name,
                })

    def _validate_pilot_to_instructor(self, pilot):
        """Validate a Pilot -> Instructor transfer.

        Args:
            pilot: Source ``fs.pilot`` record.

        Raises:
            UserError: If transfer would break role integrity or future assignments.
        """
        self._validate_source_role(pilot, 'fs.pilot')
        self._validate_target_license()
        identity = pilot.person_identity_id
        current_instructor = self.env['fs.instructor'].with_context(active_test=False).search([
            ('person_identity_id', '=', identity.id),
            ('role_state', '=', 'current'),
            ('active', '=', True),
        ], limit=1)
        if current_instructor:
            raise UserError(self.env._('This identity already has a current instructor role.'))

        source_crew = self._get_crew_member(pilot)
        scheduled_records, flight_records = self._get_future_crew_assignments(source_crew)
        if (scheduled_records or flight_records) and not self.reassign_future_assignments:
            raise UserError(self.env._(
                'This pilot has %(scheduled_count)s future scheduled flight(s) and %(flight_count)s '
                'planned/active operation(s). Enable future reassignment or clear those assignments first.'
            ) % {
                'scheduled_count': len(scheduled_records),
                'flight_count': len(flight_records),
            })

    def _create_transition(self, source):
        """Create the draft audit transition record.

        Args:
            source: Source role record.

        Returns:
            models.Model: New transition record.
        """
        values = {
            'person_identity_id': source.person_identity_id.id,
            'transition_type': self.transition_type,
            'transition_date': self.transition_date,
            'state': 'draft',
            'source_model': source._name,
            'source_res_id': source.id,
            'reason': self.reason,
            'copy_documents': self.copy_documents,
            'copy_qualifications': self.copy_qualifications,
            'reassign_future_assignments': self.reassign_future_assignments,
        }
        if source._name == 'fs.student':
            values['from_student_id'] = source.id
        elif source._name == 'fs.pilot':
            values['from_pilot_id'] = source.id
        return self.env['fs.person.role.transition'].create(values)

    def _mark_source_former(self, source, transition):
        """Archive the source role as a former role.

        Args:
            source: Source role record.
            transition: Transition audit record.
        """
        source.write({
            'role_state': 'former',
            'role_end_date': self.transition_date,
            'transition_out_id': transition.id,
            'active': False,
        })

    def _complete_transition(self, transition, target):
        """Mark the transition as completed and return the target action.

        Args:
            transition: Transition audit record.
            target: Target role record.

        Returns:
            dict: Odoo action opening the target role.
        """
        values = {
            'state': 'done',
            'target_model': target._name,
            'target_res_id': target.id,
        }
        if target._name == 'fs.pilot':
            values['to_pilot_id'] = target.id
        elif target._name == 'fs.instructor':
            values['to_instructor_id'] = target.id
        transition.write(values)
        if target.person_identity_id and target.name:
            target.person_identity_id.write({'name': target.name})
        return {
            'type': 'ir.actions.act_window',
            'res_model': target._name,
            'res_id': target.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'active_test': False},
        }

    def _transfer_student_to_pilot(self, student):
        """Execute Student -> Pilot transfer.

        Args:
            student: Source student role.

        Returns:
            dict: Odoo action opening the new pilot role.
        """
        self._validate_student_to_pilot(student)
        with self.env.cr.savepoint():
            transition = self._create_transition(student)
            self._mark_source_former(student, transition)
            pilot_values = self._copy_field_values(
                student,
                'fs.pilot',
                self.COMMON_COPY_FIELDS + self.STUDENT_TO_PILOT_COPY_FIELDS,
            )
            pilot_values.update({
                'person_identity_id': student.person_identity_id.id,
                'role_state': 'current',
                'role_start_date': self.transition_date,
                'role_end_date': False,
                'transition_in_id': transition.id,
                'active': True,
                'license_id': self.target_license_id.id,
                'license_number': self.target_license_number,
                'license_issue_date': self.target_license_issue_date,
                'callsign': self.target_callsign,
                'department_id': self.target_department_id.id if self.target_department_id else False,
                'english_level_id': self.target_english_level_id.id if self.target_english_level_id else False,
                'english_expiry': self.target_english_expiry,
            })
            pilot = self.env['fs.pilot'].create(pilot_values)
            self._copy_transition_documents(student, pilot, transition)
            return self._complete_transition(transition, pilot)

    def _transfer_pilot_to_instructor(self, pilot):
        """Execute Pilot -> Instructor transfer.

        Args:
            pilot: Source pilot role.

        Returns:
            dict: Odoo action opening the new instructor role.
        """
        self._validate_pilot_to_instructor(pilot)
        source_crew = self._get_crew_member(pilot)
        with self.env.cr.savepoint():
            transition = self._create_transition(pilot)
            self._mark_source_former(pilot, transition)
            instructor_values = self._copy_field_values(
                pilot,
                'fs.instructor',
                self.COMMON_COPY_FIELDS + self.PILOT_TO_INSTRUCTOR_COPY_FIELDS,
            )
            instructor_values.update({
                'person_identity_id': pilot.person_identity_id.id,
                'role_state': 'current',
                'role_start_date': self.transition_date,
                'role_end_date': False,
                'transition_in_id': transition.id,
                'active': True,
                'license_id': self.target_license_id.id,
                'license_number': self.target_license_number,
                'license_issue_date': self.target_license_issue_date,
                'callsign': self.target_callsign,
                'department_id': self.target_department_id.id if self.target_department_id else False,
                'english_level_id': self.target_english_level_id.id if self.target_english_level_id else False,
                'english_expiry': self.target_english_expiry,
                'total_instruction_hours': self.target_total_instruction_hours,
            })
            instructor = self.env['fs.instructor'].create(instructor_values)
            if self.copy_qualifications:
                self._copy_pilot_qualifications(pilot, instructor, transition)
            self._copy_transition_documents(pilot, instructor, transition)
            if self.reassign_future_assignments:
                self._reassign_future_crew_assignments(source_crew, instructor)
            return self._complete_transition(transition, instructor)

    def _copy_pilot_qualifications(self, pilot, instructor, transition):
        """Copy pilot qualifications to the new instructor role.

        Args:
            pilot: Source pilot role.
            instructor: Target instructor role.
            transition: Transition audit record.
        """
        Qualification = self.env['fs.person.qualification']
        for qualification in pilot.qualification_ids:
            Qualification.create({
                'instructor_id': instructor.id,
                'qualification_id': qualification.qualification_id.id,
                'issue_date': qualification.issue_date,
                'expiry_date': qualification.expiry_date,
                'notes': qualification.notes,
                'origin_qualification_id': qualification.id,
                'transition_id': transition.id,
            })

    def _copy_transition_documents(self, source, target, transition):
        """Copy applicable current documents from source to target if fs_documents is installed.

        Args:
            source: Source role record.
            target: Target role record.
            transition: Transition audit record.
        """
        if not self.copy_documents:
            return
        Document = self.env.get('fs.document')
        Version = self.env.get('fs.document.version')
        if Document is None or Version is None:
            return

        source_field = self.TARGET_ENTITY_FIELDS.get(source._name)
        target_field = self.TARGET_ENTITY_FIELDS.get(target._name)
        if not source_field or not target_field:
            return

        documents = Document.search([(source_field, '=', source.id), ('active', '=', True)])
        for document in documents:
            target_entity_code = document.ENTITY_FIELD_TO_TYPE[target_field]
            allowed_codes = set(document.document_type_id.applies_to_ids.mapped('code'))
            if allowed_codes and target_entity_code not in allowed_codes:
                continue
            existing_document = Document.search([
                (target_field, '=', target.id),
                ('document_type_id', '=', document.document_type_id.id),
            ], limit=1)
            if existing_document:
                continue
            new_document = Document.create({
                'document_type_id': document.document_type_id.id,
                target_field: target.id,
                'notes': document.notes,
            })
            current_version = document.current_version_id
            if current_version and current_version.file and current_version.filename:
                Version.create({
                    'document_id': new_document.id,
                    'version_number': 1,
                    'file': current_version.file,
                    'filename': current_version.filename,
                    'expiry_date': current_version.expiry_date,
                    'issue_date': current_version.issue_date,
                    'reference': current_version.reference,
                    'notes': self.env._('Copied during role transition %s.') % transition.display_name,
                    'is_current': True,
                })

    def _get_crew_member(self, role):
        """Return the crew-member view row for a pilot or instructor role.

        Args:
            role: Source/target role record.

        Returns:
            models.Model: Crew member recordset, possibly empty.
        """
        Crew = self.env.get('fs.crew.member')
        if Crew is None:
            return self.env['ir.model'].browse()
        return Crew.search([
            ('source_model', '=', role._name),
            ('source_id', '=', role.id),
        ], limit=1)

    def _get_future_crew_assignments(self, source_crew):
        """Find future scheduled/planned records for a source crew member.

        Args:
            source_crew: Source ``fs.crew.member`` record.

        Returns:
            tuple: Scheduled-flight recordset and flight recordset.
        """
        if not source_crew:
            return self.env['ir.model'].browse(), self.env['ir.model'].browse()

        ScheduledFlight = self.env.get('fs.scheduled.flight')
        Flight = self.env.get('fs.flight')
        scheduled_records = self.env['ir.model'].browse()
        flight_records = self.env['ir.model'].browse()
        crew_domain = ['|', ('pilot1_crew_id', '=', source_crew.id), ('pilot2_crew_id', '=', source_crew.id)]
        if ScheduledFlight is not None:
            scheduled_records = ScheduledFlight.search([
                ('date', '>=', self.transition_date),
            ] + crew_domain)
        if Flight is not None:
            flight_records = Flight.search([
                ('date', '>=', self.transition_date),
                ('status', 'in', ['scheduled', 'in_progress']),
            ] + crew_domain)
        return scheduled_records, flight_records

    def _reassign_future_crew_assignments(self, source_crew, instructor):
        """Reassign future records from the source pilot crew row to instructor row.

        Args:
            source_crew: Source pilot crew row.
            instructor: Target instructor role.

        Raises:
            UserError: If the target crew row is unavailable.
        """
        if not source_crew:
            return
        target_crew = self._get_crew_member(instructor)
        if not target_crew:
            raise UserError(self.env._('The new instructor is not available in the crew-member view.'))

        scheduled_records, flight_records = self._get_future_crew_assignments(source_crew)
        for recordset in (scheduled_records, flight_records):
            for record in recordset:
                values = {}
                if record.pilot1_crew_id.id == source_crew.id:
                    values['pilot1_crew_id'] = target_crew.id
                if record.pilot2_crew_id.id == source_crew.id:
                    values['pilot2_crew_id'] = target_crew.id
                if values:
                    record.write(values)

    def action_confirm(self):
        """Execute the selected role transfer.

        Returns:
            dict: Action opening the target role.

        Raises:
            UserError: If the transition type is unsupported.
        """
        self.ensure_one()
        source = self._get_source_record()
        if self.transition_type == 'student_to_pilot':
            return self._transfer_student_to_pilot(source)
        if self.transition_type == 'pilot_to_instructor':
            return self._transfer_pilot_to_instructor(source)
        raise UserError(self.env._('Unsupported role transition type.'))

    @api.constrains('transition_type', 'source_model')
    def _check_transition_source_model(self):
        """Ensure wizard source model matches transition type.

        Raises:
            ValidationError: If source model and transition type mismatch.
        """
        for record in self:
            if record.transition_type == 'student_to_pilot' and record.source_model != 'fs.student':
                raise ValidationError(self.env._('Student -> Pilot transitions require a student source.'))
            if record.transition_type == 'pilot_to_instructor' and record.source_model != 'fs.pilot':
                raise ValidationError(self.env._('Pilot -> Instructor transitions require a pilot source.'))
