# -*- coding: utf-8 -*-
# Part of Flight School Management System

"""Flight School Settings fs department module.

Purpose:
    Defines classes FsDepartment for central settings, shared security groups, departments, and base configuration records.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: base, base_setup, auth_signup.
    All Flight School addons consume the groups, menu roots, and shared settings defined here.
"""
from odoo import fields, models


class FsDepartment(models.Model):
    """Departments within the Flight School.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.department``.
        _description (str): Human-readable model label, ``Flight School Department``.

    Related:
        All Flight School addons consume the groups, menu roots, and shared settings defined here.
    """

    _name = 'fs.department'
    _description = 'Flight School Department'
    _order = 'sequence, name'

    name = fields.Char(string='Department Name', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    manager_id = fields.Many2one('res.users', string='Manager')
    parent_id = fields.Many2one('fs.department', string='Parent Department')
    child_ids = fields.One2many('fs.department', 'parent_id', string='Sub-Departments')
    note = fields.Text(string='Note')

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The department code must be unique!',
    )
