# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People role transition audit module.

Purpose:
    Records auditable Student -> Pilot and Pilot -> Instructor lifecycle events.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsPersonRoleTransition(models.Model):
    """Audit record for an immutable role-to-role transition."""

    _name = 'fs.person.role.transition'
    _description = 'Person Role Transition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'transition_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Description',
        compute='_compute_name',
        store=True,
    )
    person_identity_id = fields.Many2one(
        comodel_name='fs.person.identity',
        string='Person Identity',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
    )
    transition_type = fields.Selection(
        selection=[
            ('student_to_pilot', 'Student -> Pilot'),
            ('pilot_to_instructor', 'Pilot -> Instructor'),
        ],
        string='Transition Type',
        required=True,
        tracking=True,
    )
    transition_date = fields.Date(
        string='Transition Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    from_student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Source Student',
        ondelete='restrict',
        readonly=True,
    )
    from_pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Source Pilot',
        ondelete='restrict',
        readonly=True,
    )
    to_pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Target Pilot',
        ondelete='restrict',
        readonly=True,
    )
    to_instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Target Instructor',
        ondelete='restrict',
        readonly=True,
    )
    source_model = fields.Char(
        string='Source Model',
        readonly=True,
    )
    source_res_id = fields.Integer(
        string='Source Record ID',
        readonly=True,
    )
    target_model = fields.Char(
        string='Target Model',
        readonly=True,
    )
    target_res_id = fields.Integer(
        string='Target Record ID',
        readonly=True,
    )
    reason = fields.Text(
        string='Reason',
    )
    notes = fields.Text(
        string='Notes',
    )
    performed_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Performed By',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
    )
    copy_documents = fields.Boolean(
        string='Copied Documents',
        readonly=True,
    )
    copy_qualifications = fields.Boolean(
        string='Copied Qualifications',
        readonly=True,
    )
    reassign_future_assignments = fields.Boolean(
        string='Reassigned Future Assignments',
        readonly=True,
    )

    @api.depends(
        'transition_type', 'person_identity_id.name', 'from_student_id.name',
        'from_pilot_id.name', 'to_pilot_id.name', 'to_instructor_id.name'
    )
    def _compute_name(self):
        """Compute a readable transition label.

        Returns:
            None: Updates Odoo records in place.
        """
        labels = dict(self._fields['transition_type'].selection)
        for record in self:
            role_label = labels.get(record.transition_type, self.env._('Role Transition'))
            person_name = record.person_identity_id.name
            source = record.from_student_id or record.from_pilot_id
            target = record.to_pilot_id or record.to_instructor_id
            if target:
                person_name = target.display_name
            elif source:
                person_name = source.display_name
            record.name = '%s: %s' % (role_label, person_name or self.env._('Unknown Person'))

    @api.constrains(
        'transition_type', 'state', 'from_student_id', 'from_pilot_id',
        'to_pilot_id', 'to_instructor_id', 'person_identity_id'
    )
    def _check_transition_links(self):
        """Validate source and target links for completed transitions.

        Returns:
            None: Raises on invalid transition data.

        Raises:
            ValidationError: If record data violates transition invariants.
        """
        for record in self:
            if record.state == 'cancelled':
                continue
            if record.transition_type == 'student_to_pilot':
                if record.from_pilot_id or record.to_instructor_id:
                    raise ValidationError(self.env._(
                        'Student -> Pilot transitions cannot reference source pilots or target instructors.'
                    ))
                if record.state == 'done' and (not record.from_student_id or not record.to_pilot_id):
                    raise ValidationError(self.env._(
                        'A completed Student -> Pilot transition requires a source student and target pilot.'
                    ))
            elif record.transition_type == 'pilot_to_instructor':
                if record.from_student_id or record.to_pilot_id:
                    raise ValidationError(self.env._(
                        'Pilot -> Instructor transitions cannot reference source students or target pilots.'
                    ))
                if record.state == 'done' and (not record.from_pilot_id or not record.to_instructor_id):
                    raise ValidationError(self.env._(
                        'A completed Pilot -> Instructor transition requires a source pilot and target instructor.'
                    ))

            linked_roles = [
                role for role in (
                    record.from_student_id,
                    record.from_pilot_id,
                    record.to_pilot_id,
                    record.to_instructor_id,
                ) if role
            ]
            for role in linked_roles:
                if role.person_identity_id and role.person_identity_id != record.person_identity_id:
                    raise ValidationError(self.env._(
                        'All transition source and target roles must belong to the same identity.'
                    ))

    def _open_role(self, model_name, res_id):
        """Return an action opening a source or target role.

        Args:
            model_name: Odoo model name.
            res_id: Target record ID.

        Returns:
            dict: Odoo action dictionary.

        Raises:
            UserError: If the linked role does not exist.
        """
        self.ensure_one()
        if not model_name or not res_id:
            raise UserError(self.env._('No linked role is available for this transition.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': model_name,
            'res_id': res_id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'active_test': False},
        }

    def action_open_source(self):
        """Open the source role record.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        source = self.from_student_id or self.from_pilot_id
        return self._open_role(source._name if source else self.source_model, source.id if source else self.source_res_id)

    def action_open_target(self):
        """Open the target role record.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        target = self.to_pilot_id or self.to_instructor_id
        return self._open_role(target._name if target else self.target_model, target.id if target else self.target_res_id)
