# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Prior experience header workflow for manual onboarding data."""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class FsInitialExperience(models.Model):
    """Prior/manual onboarding experience for students, pilots, and instructors."""

    _name = 'fs.initial.experience'
    _description = 'Prior Experience'
    _order = 'entry_date desc, id desc'
    _rec_name = 'display_name'

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('review', 'In Review'),
            ('approved', 'Approved'),
            ('applied', 'Applied'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        index=True,
    )

    person_type = fields.Selection([
        ('instructor', 'Instructor'),
        ('pilot', 'Pilot'),
        ('student', 'Student'),
    ], string='Person Type', required=True, index=True)

    instructor_id = fields.Many2one(
        'fs.instructor',
        string='Instructor',
        ondelete='restrict',
        index=True,
    )
    pilot_id = fields.Many2one(
        'fs.pilot',
        string='Pilot',
        ondelete='restrict',
        index=True,
    )
    student_id = fields.Many2one(
        'fs.student',
        string='Student',
        ondelete='restrict',
        index=True,
    )

    line_ids = fields.One2many(
        comodel_name='fs.initial.experience.line',
        inverse_name='experience_id',
        string='Hour Details',
    )
    syllabus_completion_ids = fields.One2many(
        comodel_name='fs.prior.syllabus.completion',
        inverse_name='experience_id',
        string='Syllabus Progression',
    )

    prior_flight_hours = fields.Float(
        string='Prior Flight Hours',
        compute='_compute_prior_hour_totals',
        store=True,
    )
    prior_sim_hours = fields.Float(
        string='Prior Simulator Hours',
        compute='_compute_prior_hour_totals',
        store=True,
    )
    prior_solo_hours = fields.Float(
        string='Prior Solo Hours',
        compute='_compute_prior_hour_totals',
        store=True,
    )
    prior_instruction_hours = fields.Float(
        string='Prior Instruction Hours',
        compute='_compute_prior_hour_totals',
        store=True,
    )
    line_count = fields.Integer(
        string='Hour Line Count',
        compute='_compute_detail_counts',
    )
    syllabus_completion_count = fields.Integer(
        string='Syllabus Completion Count',
        compute='_compute_detail_counts',
    )

    # Hour fields
    initial_flight_hours = fields.Float(
        string='Flight Hours',
        help="Initial flight hours to add to total.",
    )
    initial_sim_hours = fields.Float(
        string='Simulator Hours',
        help="Initial simulator hours to add to total.",
    )
    initial_solo_hours = fields.Float(
        string='Solo Hours',
        help="Initial solo hours to add to total.",
    )
    initial_instruction_hours = fields.Float(
        string='Instruction Hours',
        help="Initial instruction hours (for instructors only).",
    )

    entry_date = fields.Date(
        string='Entry Date',
        default=fields.Date.context_today,
        required=True,
    )
    description = fields.Char(
        string='Description',
        help="Source of these hours (e.g., Previous employer, Other flight school)",
    )
    source_type = fields.Selection(
        selection=[
            ('manual', 'Manual Entry'),
            ('migration', 'Migration'),
            ('previous_school', 'Previous School'),
            ('previous_employer', 'Previous Employer'),
            ('regulator', 'Regulator Record'),
            ('other', 'Other'),
        ],
        string='Source Type',
        default='manual',
        required=True,
        index=True,
    )
    source_organization = fields.Char(
        string='Source Organization',
        help='Organization that supplied or originally recorded the prior data.',
    )
    source_reference = fields.Char(
        string='Source Reference',
        help='Reference number, logbook page, certificate, or migration batch identifier.',
    )
    date_start = fields.Date(
        string='Source Start Date',
    )
    date_end = fields.Date(
        string='Source End Date',
    )
    verified_by = fields.Many2one(
        'res.users',
        string='Verified By',
        ondelete='set null',
    )
    verified_date = fields.Date(
        string='Verified Date',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    notes = fields.Text(
        string='Notes',
    )

    is_applied = fields.Boolean(
        string='Applied',
        default=False,
        help="Whether these hours have been added to the person's totals.",
    )
    applied_date = fields.Datetime(
        string='Applied Date',
    )
    applied_by = fields.Many2one(
        'res.users',
        string='Applied By',
    )

    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    def init(self):
        """Initialize workflow values for legacy rows during registry updates."""
        self.env.cr.execute("""
            UPDATE fs_initial_experience
               SET state = CASE WHEN COALESCE(is_applied, false) THEN 'applied' ELSE 'draft' END
             WHERE state IS NULL
        """)
        self.env.cr.execute("""
            UPDATE fs_initial_experience
               SET source_type = 'manual'
             WHERE source_type IS NULL
        """)

    @api.depends('person_type', 'instructor_id', 'pilot_id', 'student_id', 'entry_date')
    def _compute_display_name(self):
        """Compute a stable display name for the prior experience header."""
        for record in self:
            person_name = ''
            if record.person_type == 'instructor' and record.instructor_id:
                person_name = record.instructor_id.name
            elif record.person_type == 'pilot' and record.pilot_id:
                person_name = record.pilot_id.name
            elif record.person_type == 'student' and record.student_id:
                person_name = record.student_id.name
            else:
                person_name = 'Unknown'

            date_str = record.entry_date.strftime('%Y-%m-%d') if record.entry_date else ''
            record.display_name = f"{person_name} - {date_str}"

    @api.depends(
        'line_ids.hour_kind',
        'line_ids.hours',
        'initial_flight_hours',
        'initial_sim_hours',
        'initial_solo_hours',
        'initial_instruction_hours',
    )
    def _compute_prior_hour_totals(self):
        """Compute detail totals while falling back to legacy aggregate fields."""
        for record in self:
            if record.line_ids:
                record.prior_flight_hours = sum(record.line_ids.filtered(
                    lambda line: line.hour_kind == 'flight').mapped('hours'))
                record.prior_sim_hours = sum(record.line_ids.filtered(
                    lambda line: line.hour_kind == 'simulator').mapped('hours'))
                record.prior_solo_hours = sum(record.line_ids.filtered(
                    lambda line: line.hour_kind == 'solo').mapped('hours'))
                record.prior_instruction_hours = sum(record.line_ids.filtered(
                    lambda line: line.hour_kind == 'instruction').mapped('hours'))
            else:
                record.prior_flight_hours = record.initial_flight_hours
                record.prior_sim_hours = record.initial_sim_hours
                record.prior_solo_hours = record.initial_solo_hours
                record.prior_instruction_hours = record.initial_instruction_hours

    @api.depends('line_ids', 'syllabus_completion_ids')
    def _compute_detail_counts(self):
        """Compute detail-line counters for smart buttons and summaries."""
        for record in self:
            record.line_count = len(record.line_ids)
            record.syllabus_completion_count = len(record.syllabus_completion_ids)

    @api.onchange('person_type')
    def _onchange_person_type(self):
        """Clear irrelevant person fields when type changes."""
        if self.person_type != 'instructor':
            self.instructor_id = False
            self.initial_instruction_hours = 0.0
        if self.person_type != 'pilot':
            self.pilot_id = False
        if self.person_type != 'student':
            self.student_id = False

    @api.onchange('date_start', 'date_end')
    def _onchange_source_dates(self):
        """Default the entry date to the latest source date when available."""
        if self.date_end:
            self.entry_date = self.date_end
        elif self.date_start:
            self.entry_date = self.date_start

    def _get_person(self):
        """Get the linked person record."""
        self.ensure_one()
        if self.person_type == 'instructor':
            return self.instructor_id
        elif self.person_type == 'pilot':
            return self.pilot_id
        elif self.person_type == 'student':
            return self.student_id
        return False

    def _has_legacy_hour_values(self):
        """Return whether legacy aggregate fields contain hours."""
        self.ensure_one()
        return any([
            self.initial_flight_hours,
            self.initial_sim_hours,
            self.initial_solo_hours,
            self.initial_instruction_hours,
        ])

    def _ensure_legacy_hour_lines(self, mark_applied=False):
        """Create detail lines from legacy aggregate fields when none exist."""
        self.ensure_one()
        if self.line_ids or not self._has_legacy_hour_values():
            return

        legacy_lines = []
        legacy_mapping = [
            ('flight', self.initial_flight_hours, 'applied_flight_hours_delta'),
            ('simulator', self.initial_sim_hours, 'applied_sim_hours_delta'),
            ('solo', self.initial_solo_hours, 'applied_solo_hours_delta'),
            ('instruction', self.initial_instruction_hours, 'applied_instruction_hours_delta'),
        ]
        for hour_kind, hours, applied_field in legacy_mapping:
            if not hours:
                continue
            line_values = {
                'experience_id': self.id,
                'hour_kind': hour_kind,
                'hours': hours,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'source_note': _('Converted from legacy aggregate hours.'),
                'count_toward_enrollment': False,
            }
            if mark_applied:
                line_values[applied_field] = hours
            legacy_lines.append(line_values)
        if legacy_lines:
            self.env['fs.initial.experience.line'].with_context(
                prior_experience_system_write=True,
            ).create(legacy_lines)

    def _check_manager_access(self):
        """Allow only flight-school managers and administrators to alter workflow state."""
        if not self.env.user.has_group('fs_core.group_flight_school_manager'):
            raise AccessError(_('Only flight school managers can approve, apply, or revert prior experience.'))

    def _validate_before_apply(self):
        """Run final validation before applying prior data to operational aggregates."""
        self.ensure_one()
        person = self._get_person()
        if not person:
            raise UserError(_('Select exactly one person before applying prior experience.'))
        if self.state != 'approved':
            raise UserError(_('Only approved prior experience records can be applied.'))
        if not self.line_ids and not self.syllabus_completion_ids and not self._has_legacy_hour_values():
            raise UserError(_('Add hour details or syllabus progression before applying prior experience.'))

    @api.constrains('person_type', 'instructor_id', 'pilot_id', 'student_id')
    def _check_person_selection(self):
        """Require exactly one person target matching the selected person type."""
        for record in self:
            selected_fields = [
                field_name for field_name in ('instructor_id', 'pilot_id', 'student_id')
                if record[field_name]
            ]
            if len(selected_fields) != 1:
                raise ValidationError(_('Select exactly one person for prior experience.'))
            expected_field = f'{record.person_type}_id'
            if selected_fields[0] != expected_field:
                raise ValidationError(_('The selected person must match the Person Type.'))

    @api.constrains(
        'initial_flight_hours',
        'initial_sim_hours',
        'initial_solo_hours',
        'initial_instruction_hours',
    )
    def _check_legacy_hours_non_negative(self):
        """Reject negative legacy aggregate hours."""
        for record in self:
            if any(hours < 0.0 for hours in (
                record.initial_flight_hours,
                record.initial_sim_hours,
                record.initial_solo_hours,
                record.initial_instruction_hours,
            )):
                raise ValidationError(_('Prior experience hours cannot be negative.'))

    @api.constrains('date_start', 'date_end')
    def _check_source_date_range(self):
        """Ensure source dates are chronological."""
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
                raise ValidationError(_('Source start date cannot be after source end date.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Keep legacy is_applied synchronized with the new workflow state."""
        for vals in vals_list:
            if vals.get('state') == 'applied':
                vals['is_applied'] = True
            elif vals.get('is_applied') and not vals.get('state'):
                vals['state'] = 'applied'
            elif vals.get('state') and vals.get('state') != 'applied':
                vals['is_applied'] = False
        return super().create(vals_list)

    def write(self, vals):
        """Block normal edits on applied records and sync legacy apply state."""
        if not self.env.context.get('prior_experience_system_write'):
            applied_records = self.filtered(lambda record: record.state == 'applied' or record.is_applied)
            if applied_records and vals:
                raise UserError(_('Revert an applied prior experience record before editing it.'))

        values = dict(vals)
        if values.get('state') == 'applied':
            values['is_applied'] = True
        elif values.get('state') and values.get('state') != 'applied':
            values['is_applied'] = False
        elif 'is_applied' in values and 'state' not in values:
            values['state'] = 'applied' if values['is_applied'] else 'draft'
        return super().write(values)

    def unlink(self):
        """Prevent deleting applied prior experience outside controlled corrections."""
        if not self.env.context.get('prior_experience_system_write'):
            if self.filtered(lambda record: record.state == 'applied' or record.is_applied):
                raise UserError(_('Revert applied prior experience before deleting it.'))
        return super().unlink()

    def action_submit_for_review(self):
        """Move draft prior experience to review."""
        for record in self:
            if record.state == 'draft':
                record.write({'state': 'review'})

    def action_approve(self):
        """Approve prior experience for application."""
        self._check_manager_access()
        today = fields.Date.context_today(self)
        for record in self:
            if record.state not in ('draft', 'review'):
                continue
            values = {'state': 'approved'}
            if not record.verified_by:
                values['verified_by'] = self.env.uid
            if not record.verified_date:
                values['verified_date'] = today
            record.write(values)

    def action_reset_to_draft(self):
        """Return a non-applied record to draft for corrections."""
        self._check_manager_access()
        for record in self:
            if record.state == 'applied' or record.is_applied:
                raise UserError(_('Revert applied prior experience before resetting it to draft.'))
            record.write({'state': 'draft'})

    def action_cancel(self):
        """Cancel a non-applied prior experience record."""
        self._check_manager_access()
        for record in self:
            if record.state == 'applied' or record.is_applied:
                raise UserError(_('Revert applied prior experience before cancelling it.'))
            record.write({'state': 'cancelled'})

    def action_apply_hours(self):
        """Apply prior hours and syllabus progression without creating flights."""
        self._check_manager_access()
        for record in self:
            if record.state == 'applied' or record.is_applied:
                if record.state != 'applied':
                    record.with_context(prior_experience_system_write=True).write({'state': 'applied'})
                continue
            record._validate_before_apply()
            record._ensure_legacy_hour_lines()
            person = record._get_person()
            for line in record.line_ids:
                line._apply_prior_hours(person)
            for completion in record.syllabus_completion_ids:
                completion._apply_prior_completion()
            record.with_context(prior_experience_system_write=True).write({
                'state': 'applied',
                'is_applied': True,
                'applied_date': fields.Datetime.now(),
                'applied_by': self.env.uid,
            })

    def action_revert_hours(self):
        """Revert only the deltas recorded by this prior experience."""
        self._check_manager_access()
        for record in self:
            if record.state != 'applied' and not record.is_applied:
                continue
            record._ensure_legacy_hour_lines(mark_applied=True)
            person = record._get_person()
            for completion in reversed(record.syllabus_completion_ids):
                completion._revert_prior_completion()
            for line in reversed(record.line_ids):
                line._revert_prior_hours(person)
            record.with_context(prior_experience_system_write=True).write({
                'state': 'approved',
                'is_applied': False,
                'applied_date': False,
                'applied_by': False,
            })
