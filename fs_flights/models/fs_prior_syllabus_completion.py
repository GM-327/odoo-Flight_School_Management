# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Prior syllabus completion records for manual onboarding data."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsPriorSyllabusCompletion(models.Model):
    """Line-level prior mission completions linked to prior experience."""

    _name = 'fs.prior.syllabus.completion'
    _description = 'Prior Syllabus Completion'
    _order = 'completion_date desc, id desc'
    _rec_name = 'display_name'

    experience_id = fields.Many2one(
        comodel_name='fs.initial.experience',
        string='Prior Experience',
        required=True,
        ondelete='cascade',
        index=True,
    )
    state = fields.Selection(
        related='experience_id.state',
        string='Status',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        related='experience_id.company_id',
        string='Company',
        store=True,
        readonly=True,
    )
    person_type = fields.Selection(
        related='experience_id.person_type',
        string='Person Type',
        store=True,
        readonly=True,
    )
    instructor_person_id = fields.Many2one(
        related='experience_id.instructor_id',
        string='Instructor Person',
        store=True,
        readonly=True,
    )
    pilot_id = fields.Many2one(
        related='experience_id.pilot_id',
        string='Pilot',
        store=True,
        readonly=True,
    )
    student_id = fields.Many2one(
        related='experience_id.student_id',
        string='Student',
        store=True,
        readonly=True,
    )
    enrollment_id = fields.Many2one(
        comodel_name='fs.student.enrollment',
        string='Enrollment',
        required=True,
        ondelete='restrict',
        index=True,
    )
    mission_id = fields.Many2one(
        comodel_name='fs.flight.mission',
        string='Mission',
        required=True,
        ondelete='restrict',
        index=True,
    )
    completion_date = fields.Date(
        string='Completion Date',
        default=fields.Date.context_today,
        required=True,
    )
    instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Recorded Instructor',
        ondelete='set null',
    )
    source_organization = fields.Char(
        string='Source Organization',
    )
    source_reference = fields.Char(
        string='Source Reference',
    )
    notes = fields.Text(
        string='Notes',
    )
    generated_completion_id = fields.Many2one(
        comodel_name='fs.mission.completion',
        string='Mission Completion',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    completion_was_created = fields.Boolean(
        string='Created Completion',
        readonly=True,
        copy=False,
    )
    previous_is_completed = fields.Boolean(readonly=True, copy=False)
    previous_completion_date = fields.Date(readonly=True, copy=False)
    previous_source = fields.Selection(
        selection=[
            ('manual', 'Manual'),
            ('operational_flight', 'Operational Flight'),
            ('prior_experience', 'Prior Experience'),
        ],
        readonly=True,
        copy=False,
    )
    previous_source_organization = fields.Char(readonly=True, copy=False)
    previous_source_reference = fields.Char(readonly=True, copy=False)
    previous_source_date = fields.Date(readonly=True, copy=False)
    previous_source_notes = fields.Text(readonly=True, copy=False)
    previous_is_prior_experience = fields.Boolean(readonly=True, copy=False)
    previous_source_record_model = fields.Char(readonly=True, copy=False)
    previous_source_record_id = fields.Integer(readonly=True, copy=False)
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    _unique_prior_completion = models.Constraint(
        'UNIQUE(experience_id, enrollment_id, mission_id)',
        'This mission is already recorded for this prior experience and enrollment.',
    )

    @api.depends('enrollment_id.display_name', 'mission_id.name', 'completion_date')
    def _compute_display_name(self):
        """Compute prior syllabus completion display names."""
        for record in self:
            enrollment_name = record.enrollment_id.display_name or _('Enrollment')
            mission_name = record.mission_id.name or _('Mission')
            record.display_name = f'{enrollment_name} - {mission_name}'

    @api.onchange('experience_id')
    def _onchange_experience_id(self):
        """Default source fields from the prior-experience header."""
        if self.experience_id:
            self.source_organization = self.experience_id.source_organization
            self.source_reference = self.experience_id.source_reference

    @api.constrains('experience_id', 'enrollment_id')
    def _check_enrollment_person(self):
        """Require the completion enrollment to belong to the header person."""
        for record in self:
            if record.person_type == 'student' and record.enrollment_id.student_id != record.student_id:
                raise ValidationError(_('The syllabus enrollment must belong to the selected student.'))
            if record.person_type == 'pilot' and record.enrollment_id.pilot_id != record.pilot_id:
                raise ValidationError(_('The syllabus enrollment must belong to the selected pilot.'))
            if record.person_type == 'instructor' and record.enrollment_id.enrolled_instructor_id != record.instructor_person_id:
                raise ValidationError(_('The syllabus enrollment must belong to the selected instructor.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Block adding syllabus lines to applied records outside internals."""
        if not self.env.context.get('prior_experience_system_write'):
            experience_ids = [vals.get('experience_id') for vals in vals_list if vals.get('experience_id')]
            applied_experience = self.env['fs.initial.experience'].browse(experience_ids).filtered(
                lambda record: record.state == 'applied' or record.is_applied
            )
            if applied_experience:
                raise UserError(_('Revert applied prior experience before adding syllabus lines.'))
        return super().create(vals_list)

    def write(self, vals):
        """Block editing applied syllabus lines outside apply/revert internals."""
        if not self.env.context.get('prior_experience_system_write'):
            applied_records = self.filtered(lambda record: record.state == 'applied' or record.experience_id.is_applied)
            if applied_records and vals:
                raise UserError(_('Revert applied prior experience before editing syllabus lines.'))
        return super().write(vals)

    def unlink(self):
        """Block deleting applied syllabus lines outside controlled corrections."""
        if not self.env.context.get('prior_experience_system_write'):
            applied_records = self.filtered(lambda record: record.state == 'applied' or record.experience_id.is_applied)
            if applied_records:
                raise UserError(_('Revert applied prior experience before deleting syllabus lines.'))
        return super().unlink()

    def _source_values(self):
        """Build generic source metadata for fs.mission.completion."""
        self.ensure_one()
        source_organization = self.source_organization or self.experience_id.source_organization
        source_reference = self.source_reference or self.experience_id.source_reference
        source_notes = self.notes or self.experience_id.notes
        return {
            'is_completed': True,
            'completion_date': self.completion_date,
            'source': 'prior_experience',
            'source_organization': source_organization,
            'source_reference': source_reference,
            'source_date': self.completion_date or self.experience_id.date_end or self.experience_id.entry_date,
            'source_notes': source_notes,
            'is_prior_experience': True,
            'source_record_model': self._name,
            'source_record_id': self.id,
        }

    def _previous_values(self, mission_completion):
        """Capture existing mission completion metadata before applying prior data."""
        return {
            'previous_is_completed': mission_completion.is_completed,
            'previous_completion_date': mission_completion.completion_date,
            'previous_source': mission_completion.source,
            'previous_source_organization': mission_completion.source_organization,
            'previous_source_reference': mission_completion.source_reference,
            'previous_source_date': mission_completion.source_date,
            'previous_source_notes': mission_completion.source_notes,
            'previous_is_prior_experience': mission_completion.is_prior_experience,
            'previous_source_record_model': mission_completion.source_record_model,
            'previous_source_record_id': mission_completion.source_record_id,
        }

    def _restore_values(self):
        """Return stored mission completion values for revert."""
        self.ensure_one()
        return {
            'is_completed': self.previous_is_completed,
            'completion_date': self.previous_completion_date,
            'source': self.previous_source or 'manual',
            'source_organization': self.previous_source_organization,
            'source_reference': self.previous_source_reference,
            'source_date': self.previous_source_date,
            'source_notes': self.previous_source_notes,
            'is_prior_experience': self.previous_is_prior_experience,
            'source_record_model': self.previous_source_record_model,
            'source_record_id': self.previous_source_record_id,
        }

    def _clear_apply_metadata(self):
        """Clear stored apply/revert metadata on the prior syllabus line."""
        self.with_context(prior_experience_system_write=True).write({
            'generated_completion_id': False,
            'completion_was_created': False,
            'previous_is_completed': False,
            'previous_completion_date': False,
            'previous_source': False,
            'previous_source_organization': False,
            'previous_source_reference': False,
            'previous_source_date': False,
            'previous_source_notes': False,
            'previous_is_prior_experience': False,
            'previous_source_record_model': False,
            'previous_source_record_id': False,
        })

    def _apply_prior_completion(self):
        """Create or update fs.mission.completion for this prior syllabus line."""
        self.ensure_one()
        if self.generated_completion_id:
            return

        MissionCompletion = self.env['fs.mission.completion'].sudo()
        mission_completion = MissionCompletion.search([
            ('enrollment_id', '=', self.enrollment_id.id),
            ('mission_id', '=', self.mission_id.id),
        ], limit=1)
        source_values = self._source_values()
        if mission_completion:
            line_values = self._previous_values(mission_completion)
            line_values.update({
                'generated_completion_id': mission_completion.id,
                'completion_was_created': False,
            })
            self.with_context(prior_experience_system_write=True).write(line_values)
            mission_completion.write(source_values)
        else:
            mission_completion = MissionCompletion.create({
                'enrollment_id': self.enrollment_id.id,
                'mission_id': self.mission_id.id,
                **source_values,
            })
            self.with_context(prior_experience_system_write=True).write({
                'generated_completion_id': mission_completion.id,
                'completion_was_created': True,
            })

    def _revert_prior_completion(self):
        """Undo source changes made by this prior syllabus line when safe."""
        self.ensure_one()
        mission_completion = self.generated_completion_id
        if not mission_completion:
            return

        is_same_prior_source = (
            mission_completion.source == 'prior_experience'
            and mission_completion.source_record_model == self._name
            and mission_completion.source_record_id == self.id
        )
        if self.completion_was_created:
            if is_same_prior_source:
                mission_completion.sudo().unlink()
        elif is_same_prior_source:
            mission_completion.sudo().write(self._restore_values())

        self._clear_apply_metadata()
