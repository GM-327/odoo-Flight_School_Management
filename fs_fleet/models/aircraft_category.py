# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Fleet aircraft category module.

Purpose:
    Defines classes AircraftCategory for aircraft categories, aircraft types, aircraft records, maintenance awareness, and fleet dashboard data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, mail.
    fs_training defines aircraft-type requirements.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AircraftCategory(models.Model):
    """Aircraft category classification (single-engine, multi-engine, etc.).

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.aircraft.category``.
        _inherit: Odoo model(s) extended by this class: ``['mail.thread']``.
        _description (str): Human-readable model label, ``Aircraft Category``.

    Related:
        fs_training defines aircraft-type requirements.
        fs_scheduling and fs_flights use aircraft availability and total-hour data.
    """

    _name = 'fs.aircraft.category'
    _description = 'Aircraft Category'
    _inherit = ['mail.thread']
    _order = 'sequence, name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help="Name of the aircraft category.",
    )
    code = fields.Char(
        string='Code',
        required=True,
        help="Short code for the category (e.g., SEP, MEP).",
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help="Detailed description of this aircraft category.",
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Order in lists and dropdowns.",
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color index for kanban views.",
    )
    aircraft_type_ids = fields.One2many(
        comodel_name='fs.aircraft.type',
        inverse_name='category_id',
        string='Aircraft Types',
        help="Types of aircraft in this category.",
    )
    aircraft_type_count = fields.Integer(
        string='Types Count',
        compute='_compute_aircraft_type_count',
        store=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this category.",
    )
    is_simulator = fields.Boolean(
        string='Is Simulator',
        default=False,
    )

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Category code must be unique!',
    )
    _name_unique = models.Constraint(
        'UNIQUE(name)',
        'Category name must be unique!',
    )

    @api.model
    def _normalize_write_vals(self, vals):
        """Apply category normalization rules to create/write values."""
        normalized = dict(vals)
        if 'code' in normalized and normalized['code']:
            normalized['code'] = normalized['code'].strip().upper()
        return normalized

    @api.depends('aircraft_type_ids')
    def _compute_aircraft_type_count(self):
        """Compute aircraft type count values for the current recordset.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        for record in self:
            record.aircraft_type_count = len(record.aircraft_type_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Normalize category values before creation."""
        normalized_vals_list = [self._normalize_write_vals(vals) for vals in vals_list]
        return super().create(normalized_vals_list)

    def write(self, vals):
        """Normalize category values before writing."""
        return super().write(self._normalize_write_vals(vals))

    @api.constrains('code')
    def _check_code_uppercase(self):
        """Validate code uppercase business rules.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            UserError: If user-facing business validation fails.
        """
        for record in self:
            if record.code and record.code != record.code.upper():
                raise ValidationError(_('Category code must be uppercase.'))

    @api.onchange('code')
    def _onchange_code_uppercase(self):
        """Update form values when code uppercase changes.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.
        """
        if self.code:
            self.code = self.code.upper()

    def unlink(self):
        """Delete records after enforcing Flight School business safeguards.

        Returns:
            bool: True when Odoo successfully deletes the records.

        Raises:
            UserError: If user-facing business validation fails.
        """
        for record in self:
            if record.aircraft_type_ids:
                raise UserError(
                    _(
                        "Cannot delete category '%(name)s' because it has %(count)s aircraft type(s) assigned. "
                        "Archive it instead.",
                        name=record.name,
                        count=len(record.aircraft_type_ids),
                    )
                )
        return super().unlink()
