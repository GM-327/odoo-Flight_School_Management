# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Training fs admin task module.

Purpose:
    Defines classes FsAdminTaskTemplate, FsClassTypeAdminTask, FsAdminTask for class types, training classes, enrollments, missions, activities, completion tracking, and training KPIs.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_people, fs_fleet, mail.
    fs_scheduling schedules training missions.
"""
from odoo import api, fields, models


class FsAdminTaskTemplate(models.Model):
    """General admin task templates - a library of suggested tasks.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.admin.task.template``.
        _description (str): Human-readable model label, ``Admin Task Template``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

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
    """Intermediate model linking class types to admin task templates with sequence.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.class.type.admin.task``.
        _description (str): Human-readable model label, ``Class Type Admin Task``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

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
    """Admin task instances for training classes.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.admin.task``.
        _description (str): Human-readable model label, ``Admin Task``.

    Related:
        fs_scheduling schedules training missions.
        fs_flights posts completed hours back to enrollments.
    """

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
        """Set or clear done date and user when toggling done status.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            if record.is_done:
                record.done_date = fields.Date.context_today(record)
                record.done_by_id = self.env.user
            else:
                record.done_date = False
                record.done_by_id = False
