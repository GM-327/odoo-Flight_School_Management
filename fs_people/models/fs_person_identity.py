# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School People person identity module.

Purpose:
    Groups historical and current role records that represent the same person.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training, fs_scheduling, fs_flights, and fs_documents keep role-specific
    historical references.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class FsPersonIdentity(models.Model):
    """Stable identity grouping student, pilot, and instructor role records.

    Role records remain immutable historical snapshots. This model provides the
    lifecycle thread that connects those snapshots across transitions.
    """

    _name = 'fs.person.identity'
    _description = 'Flight School Person Identity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    current_role = fields.Selection(
        selection=[
            ('student', 'Student'),
            ('pilot', 'Pilot'),
            ('instructor', 'Instructor'),
        ],
        string='Current Role',
        compute='_compute_role_links',
        store=True,
    )
    current_student_id = fields.Many2one(
        comodel_name='fs.student',
        string='Current Student',
        compute='_compute_role_links',
        store=True,
    )
    current_pilot_id = fields.Many2one(
        comodel_name='fs.pilot',
        string='Current Pilot',
        compute='_compute_role_links',
        store=True,
    )
    current_instructor_id = fields.Many2one(
        comodel_name='fs.instructor',
        string='Current Instructor',
        compute='_compute_role_links',
        store=True,
    )
    student_ids = fields.One2many(
        comodel_name='fs.student',
        inverse_name='person_identity_id',
        string='Student Roles',
        context={'active_test': False},
    )
    pilot_ids = fields.One2many(
        comodel_name='fs.pilot',
        inverse_name='person_identity_id',
        string='Pilot Roles',
        context={'active_test': False},
    )
    instructor_ids = fields.One2many(
        comodel_name='fs.instructor',
        inverse_name='person_identity_id',
        string='Instructor Roles',
        context={'active_test': False},
    )
    transition_ids = fields.One2many(
        comodel_name='fs.person.role.transition',
        inverse_name='person_identity_id',
        string='Role Transitions',
    )
    student_count = fields.Integer(
        string='Student Roles',
        compute='_compute_role_counts',
    )
    pilot_count = fields.Integer(
        string='Pilot Roles',
        compute='_compute_role_counts',
    )
    instructor_count = fields.Integer(
        string='Instructor Roles',
        compute='_compute_role_counts',
    )
    transition_count = fields.Integer(
        string='Transitions',
        compute='_compute_role_counts',
    )
    identification_number = fields.Char(
        string='ID Number',
        help='Optional canonical ID/passport number used for searching identities.',
    )
    service_number = fields.Char(
        string='Service Number',
        help='Optional canonical military/personnel number used for searching identities.',
    )
    birth_date = fields.Date(
        string='Date of Birth',
    )
    nationality_id = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
    )

    @api.depends(
        'student_ids.active', 'student_ids.role_state',
        'pilot_ids.active', 'pilot_ids.role_state',
        'instructor_ids.active', 'instructor_ids.role_state',
    )
    def _compute_role_links(self):
        """Compute current role helper links for each identity.

        Returns:
            None: Updates Odoo records in place.
        """
        for record in self:
            student = record.with_context(active_test=False).student_ids.filtered(
                lambda role: role.is_current_role
            )[:1]
            pilot = record.with_context(active_test=False).pilot_ids.filtered(
                lambda role: role.is_current_role
            )[:1]
            instructor = record.with_context(active_test=False).instructor_ids.filtered(
                lambda role: role.is_current_role
            )[:1]

            record.current_student_id = student
            record.current_pilot_id = pilot
            record.current_instructor_id = instructor
            if instructor:
                record.current_role = 'instructor'
            elif pilot:
                record.current_role = 'pilot'
            elif student:
                record.current_role = 'student'
            else:
                record.current_role = False

    def _compute_role_counts(self):
        """Compute role and transition counters for smart buttons.

        Returns:
            None: Updates Odoo records in place.
        """
        for record in self:
            record_ctx = record.with_context(active_test=False)
            record.student_count = len(record_ctx.student_ids)
            record.pilot_count = len(record_ctx.pilot_ids)
            record.instructor_count = len(record_ctx.instructor_ids)
            record.transition_count = len(record.transition_ids)

    def _role_action(self, model_name, role_name):
        """Return an action opening all roles of one type for this identity.

        Args:
            model_name: Odoo model name to open.
            role_name: Human-readable role label.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        return {
            'name': self.env._('%s History') % role_name,
            'type': 'ir.actions.act_window',
            'res_model': model_name,
            'view_mode': 'list,form',
            'domain': [('person_identity_id', '=', self.id)],
            'context': {'active_test': False, 'default_person_identity_id': self.id},
        }

    def action_view_students(self):
        """Open student role history for this identity.

        Returns:
            dict: Odoo action dictionary.
        """
        return self._role_action('fs.student', 'Student')

    def action_view_pilots(self):
        """Open pilot role history for this identity.

        Returns:
            dict: Odoo action dictionary.
        """
        return self._role_action('fs.pilot', 'Pilot')

    def action_view_instructors(self):
        """Open instructor role history for this identity.

        Returns:
            dict: Odoo action dictionary.
        """
        return self._role_action('fs.instructor', 'Instructor')

    def action_view_transitions(self):
        """Open transition audit records for this identity.

        Returns:
            dict: Odoo action dictionary.
        """
        self.ensure_one()
        return {
            'name': self.env._('Role Transitions'),
            'type': 'ir.actions.act_window',
            'res_model': 'fs.person.role.transition',
            'view_mode': 'list,form',
            'domain': [('person_identity_id', '=', self.id)],
            'context': {'default_person_identity_id': self.id},
        }

    def action_view_current_role(self):
        """Open the current operational role for this identity.

        Returns:
            dict: Odoo action dictionary.

        Raises:
            UserError: If no current role exists.
        """
        self.ensure_one()
        role_record = self.current_instructor_id or self.current_pilot_id or self.current_student_id
        if not role_record:
            raise UserError(self.env._('This identity has no current role.'))
        return {
            'type': 'ir.actions.act_window',
            'res_model': role_record._name,
            'res_id': role_record.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'active_test': False},
        }
