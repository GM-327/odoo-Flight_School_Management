# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class FsClassRequirement(models.Model):
    """Enrollment requirements for training classes."""

    _name = 'fs.class.requirement'
    _description = 'Class Requirement'
    _order = 'name'

    name = fields.Char(
        string='Name',
        required=True,
        help="Requirement name (e.g., Valid Medical, PPL License).",
    )
    category = fields.Selection(
        selection=[
            ('medical', 'Medical'),
            ('license', 'License'),
            ('qualification', 'Qualification'),
            ('english', 'English Proficiency'),
            ('security_clearance', 'Security Clearance'),
            ('insurance', 'Insurance'),
            ('other', 'Other / Manual Check'),
        ],
        string='Category',
        default='other',
        help="Link to expiry-tracked field for automatic validation.",
    )
    is_military = fields.Boolean(
        string='Military',
        default=True,
        help="Applies to military students.",
    )
    is_civilian = fields.Boolean(
        string='Civilian',
        default=True,
        help="Applies to civilian students.",
    )
    is_default = fields.Boolean(
        string='Default',
        default=False,
        help="Automatically add to new class types.",
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
