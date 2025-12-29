# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models


class FsAdminTaskTemplate(models.Model):
    """General admin task templates - a library of suggested tasks."""

    _name = 'fs.admin.task.template'
    _description = 'Admin Task Template'
    _order = 'sequence, name'

    name = fields.Char(
        string='Task Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Default sequence (can be overridden per class type).",
    )
    description = fields.Text(
        string='Instructions',
    )
    notes = fields.Char(
        string='Notes/Reference',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    is_default = fields.Boolean(
        string='Default Task',
        default=False,
        help="If enabled, this task will be automatically added to every new class type.",
    )


class FsClassTypeAdminTask(models.Model):
    """Intermediate model linking class types to admin task templates with sequence."""

    _name = 'fs.class.type.admin.task'
    _description = 'Class Type Admin Task'
    _order = 'sequence, id'

    class_type_id = fields.Many2one(
        comodel_name='fs.class.type',
        string='Class Type',
        required=True,
        ondelete='cascade',
    )
    template_id = fields.Many2one(
        comodel_name='fs.admin.task.template',
        string='Task Template',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    # Related fields for display
    template_name = fields.Char(
        string='Task Name',
        related='template_id.name',
    )
    template_description = fields.Text(
        string='Instructions',
        related='template_id.description',
    )
    notes = fields.Char(
        string='Notes/Reference',
    )


class FsAdminTask(models.Model):
    """Admin task instances for training classes."""

    _name = 'fs.admin.task'
    _description = 'Admin Task'
    _order = 'sequence, id'

    name = fields.Char(
        string='Task Name',
        required=True,
    )
    training_class_id = fields.Many2one(
        comodel_name='fs.training.class',
        string='Training Class',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    description = fields.Text(
        string='Instructions',
    )
    notes = fields.Char(
        string='Notes/Reference',
    )
    is_done = fields.Boolean(
        string='Done',
        default=False,
    )
    done_date = fields.Date(
        string='Done Date',
    )
    done_by_id = fields.Many2one(
        comodel_name='res.users',
        string='Done By',
    )

    @api.onchange('is_done')
    def _onchange_is_done(self):
        """Set or clear done date and user when toggling done status."""
        for record in self:
            if record.is_done:
                record.done_date = fields.Date.context_today(record)
                record.done_by_id = self.env.user
            else:
                record.done_date = False
                record.done_by_id = False
