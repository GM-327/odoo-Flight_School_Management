# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Detailed prior-hour lines for manual onboarding experience."""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsInitialExperienceLine(models.Model):
    """Line-level prior hours with exact applied deltas."""

    _name = 'fs.initial.experience.line'
    _description = 'Prior Experience Hour Line'
    _order = 'experience_id, date_end desc, id'
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
    instructor_id = fields.Many2one(
        related='experience_id.instructor_id',
        string='Instructor',
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
        ondelete='restrict',
        index=True,
        help='Optional enrollment whose progression should receive this prior activity time.',
    )
    activity_id = fields.Many2one(
        comodel_name='fs.flight.activity',
        string='Activity',
        ondelete='restrict',
    )
    aircraft_category_id = fields.Many2one(
        comodel_name='fs.aircraft.category',
        string='Aircraft Category',
        ondelete='set null',
    )
    aircraft_type_id = fields.Many2one(
        comodel_name='fs.aircraft.type',
        string='Aircraft Type',
        ondelete='set null',
    )
    hour_kind = fields.Selection(
        selection=[
            ('flight', 'Flight'),
            ('simulator', 'Simulator'),
            ('solo', 'Solo'),
            ('instruction', 'Instruction'),
        ],
        string='Hour Kind',
        default='flight',
        required=True,
        index=True,
    )
    hours = fields.Float(
        string='Hours',
        required=True,
        default=0.0,
    )
    date_start = fields.Date(
        string='Start Date',
    )
    date_end = fields.Date(
        string='End Date',
    )
    source_note = fields.Char(
        string='Source Note',
    )
    count_toward_enrollment = fields.Boolean(
        string='Count Toward Enrollment',
        default=True,
        help='When checked, this line updates the matching enrollment activity hours.',
    )

    applied_flight_hours_delta = fields.Float(
        string='Applied Flight Delta',
        readonly=True,
        copy=False,
    )
    applied_sim_hours_delta = fields.Float(
        string='Applied Simulator Delta',
        readonly=True,
        copy=False,
    )
    applied_solo_hours_delta = fields.Float(
        string='Applied Solo Delta',
        readonly=True,
        copy=False,
    )
    applied_instruction_hours_delta = fields.Float(
        string='Applied Instruction Delta',
        readonly=True,
        copy=False,
    )
    applied_enrollment_hour_id = fields.Many2one(
        comodel_name='fs.enrollment.hours',
        string='Applied Enrollment Hour Row',
        readonly=True,
        copy=False,
        ondelete='set null',
    )
    applied_enrollment_hours_delta = fields.Float(
        string='Applied Enrollment Delta',
        readonly=True,
        copy=False,
    )
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
    )

    @api.depends('experience_id.display_name', 'hour_kind', 'hours', 'activity_id.display_name')
    def _compute_display_name(self):
        """Compute a compact line label."""
        for line in self:
            activity_name = line.activity_id.display_name or _('No Activity')
            line.display_name = _('%(kind)s %(hours).2f h - %(activity)s') % {
                'kind': dict(line._fields['hour_kind'].selection).get(line.hour_kind, line.hour_kind),
                'hours': line.hours,
                'activity': activity_name,
            }

    @api.onchange('aircraft_type_id')
    def _onchange_aircraft_type_id(self):
        """Populate category from the selected aircraft type."""
        if self.aircraft_type_id:
            self.aircraft_category_id = self.aircraft_type_id.category_id

    @api.onchange('hour_kind')
    def _onchange_hour_kind(self):
        """Default enrollment counting to total activity hour kinds."""
        if self.hour_kind in ('solo', 'instruction'):
            self.count_toward_enrollment = False
        elif self.hour_kind in ('flight', 'simulator'):
            self.count_toward_enrollment = True

    @api.constrains('hours')
    def _check_hours_non_negative(self):
        """Reject negative prior-hour lines."""
        for line in self:
            if line.hours < 0.0:
                raise ValidationError(_('Prior experience hours cannot be negative.'))

    @api.constrains('date_start', 'date_end')
    def _check_line_date_range(self):
        """Ensure line dates are chronological."""
        for line in self:
            if line.date_start and line.date_end and line.date_start > line.date_end:
                raise ValidationError(_('Line start date cannot be after line end date.'))

    @api.constrains('hour_kind', 'experience_id')
    def _check_instruction_person_type(self):
        """Instruction-hour totals are only supported on instructors."""
        for line in self:
            if line.hour_kind == 'instruction' and line.person_type != 'instructor':
                raise ValidationError(_('Instruction hours can only be recorded for instructors.'))

    @api.constrains('enrollment_id', 'activity_id', 'count_toward_enrollment', 'experience_id')
    def _check_enrollment_link(self):
        """Validate optional progression links against the header person."""
        for line in self:
            if line.count_toward_enrollment and line.enrollment_id and not line.activity_id:
                raise ValidationError(_('Select an activity when a prior-hour line counts toward enrollment.'))
            if not line.enrollment_id:
                continue
            if line.person_type == 'student' and line.enrollment_id.student_id != line.student_id:
                raise ValidationError(_('The enrollment must belong to the selected student.'))
            if line.person_type == 'pilot' and line.enrollment_id.pilot_id != line.pilot_id:
                raise ValidationError(_('The enrollment must belong to the selected pilot.'))
            if line.person_type == 'instructor' and line.enrollment_id.enrolled_instructor_id != line.instructor_id:
                raise ValidationError(_('The enrollment must belong to the selected instructor.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Block adding lines to applied records outside controlled conversions."""
        if not self.env.context.get('prior_experience_system_write'):
            experience_ids = [vals.get('experience_id') for vals in vals_list if vals.get('experience_id')]
            applied_experience = self.env['fs.initial.experience'].browse(experience_ids).filtered(
                lambda record: record.state == 'applied' or record.is_applied
            )
            if applied_experience:
                raise UserError(_('Revert applied prior experience before adding hour lines.'))
        return super().create(vals_list)

    def write(self, vals):
        """Block editing applied prior-hour lines outside apply/revert internals."""
        if not self.env.context.get('prior_experience_system_write'):
            applied_lines = self.filtered(lambda line: line.state == 'applied' or line.experience_id.is_applied)
            if applied_lines and vals:
                raise UserError(_('Revert applied prior experience before editing hour lines.'))
        return super().write(vals)

    def unlink(self):
        """Block deleting applied prior-hour lines outside controlled corrections."""
        if not self.env.context.get('prior_experience_system_write'):
            applied_lines = self.filtered(lambda line: line.state == 'applied' or line.experience_id.is_applied)
            if applied_lines:
                raise UserError(_('Revert applied prior experience before deleting hour lines.'))
        return super().unlink()

    def _person_delta_field(self):
        """Return the person total field and stored delta field for this hour kind."""
        self.ensure_one()
        return {
            'flight': ('total_flight_hours', 'applied_flight_hours_delta'),
            'simulator': ('total_sim_hours', 'applied_sim_hours_delta'),
            'solo': ('solo_hours', 'applied_solo_hours_delta'),
            'instruction': ('total_instruction_hours', 'applied_instruction_hours_delta'),
        }.get(self.hour_kind, (False, False))

    def _find_enrollment_hour(self):
        """Find the enrollment hour bucket, preferring mandatory before extra."""
        self.ensure_one()
        EnrollmentHours = self.env['fs.enrollment.hours']
        enrollment_hour = EnrollmentHours.search([
            ('enrollment_id', '=', self.enrollment_id.id),
            ('activity_id', '=', self.activity_id.id),
            ('is_extra', '=', False),
        ], limit=1)
        if enrollment_hour:
            return enrollment_hour
        return EnrollmentHours.search([
            ('enrollment_id', '=', self.enrollment_id.id),
            ('activity_id', '=', self.activity_id.id),
            ('is_extra', '=', True),
        ], limit=1)

    def _apply_prior_hours(self, person):
        """Apply stored prior-hour deltas to person totals and enrollment progression."""
        self.ensure_one()
        if self.hours <= 0.0:
            return

        person_field, delta_field = self._person_delta_field()
        if person and person_field and delta_field and not self[delta_field] and hasattr(person, person_field):
            current_hours = person[person_field] or 0.0
            person.sudo().write({person_field: current_hours + self.hours})
            self.with_context(prior_experience_system_write=True).write({delta_field: self.hours})

        self._apply_enrollment_hours()

    def _apply_enrollment_hours(self):
        """Apply this line to enrollment activity progress when requested."""
        self.ensure_one()
        if (
            not self.count_toward_enrollment
            or not self.enrollment_id
            or not self.activity_id
            or self.hours <= 0.0
            or self.applied_enrollment_hours_delta
        ):
            return

        enrollment_hour = self._find_enrollment_hour()
        if enrollment_hour:
            enrollment_hour.sudo().write({'hours_logged': enrollment_hour.hours_logged + self.hours})
        else:
            enrollment_hour = self.env['fs.enrollment.hours'].sudo().create({
                'enrollment_id': self.enrollment_id.id,
                'activity_id': self.activity_id.id,
                'hours_logged': self.hours,
                'is_extra': True,
            })
        self.with_context(prior_experience_system_write=True).write({
            'applied_enrollment_hour_id': enrollment_hour.id,
            'applied_enrollment_hours_delta': self.hours,
        })

    def _revert_prior_hours(self, person):
        """Revert stored prior-hour deltas from totals and enrollment progress."""
        self.ensure_one()
        person_field, delta_field = self._person_delta_field()
        values_to_clear = {}
        if person and person_field and delta_field and self[delta_field] and hasattr(person, person_field):
            current_hours = person[person_field] or 0.0
            person.sudo().write({person_field: max(0.0, current_hours - self[delta_field])})
            values_to_clear[delta_field] = 0.0

        if self.applied_enrollment_hour_id and self.applied_enrollment_hours_delta:
            enrollment_hour = self.applied_enrollment_hour_id
            new_hours = max(0.0, enrollment_hour.hours_logged - self.applied_enrollment_hours_delta)
            enrollment_hour.sudo().write({'hours_logged': new_hours})
            values_to_clear.update({
                'applied_enrollment_hour_id': False,
                'applied_enrollment_hours_delta': 0.0,
            })

        if values_to_clear:
            self.with_context(prior_experience_system_write=True).write(values_to_clear)
