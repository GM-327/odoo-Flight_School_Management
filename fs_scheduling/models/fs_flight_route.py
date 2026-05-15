# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Scheduling fs flight route module.

Purpose:
    Defines classes FsFlightRoute for planned flights, crew selection, route management, scheduling wizards, conflict detection, and timeline data.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_core, fs_training, fs_fleet, fs_people, mail, web_timeline.
    fs_flights publishes scheduled plans to operations boards.
"""
from odoo import api, fields, models
from odoo.fields import Domain


class FsFlightRoute(models.Model):
    """Specific working areas or flight routes used for scheduling.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _name (str): Odoo model identifier ``fs.flight.route``.
        _description (str): Human-readable model label, ``Flight Route / Area``.

    Related:
        fs_flights publishes scheduled plans to operations boards.
        fs_fleet supplies aircraft availability.
    """
    _name = 'fs.flight.route'
    _description = 'Flight Route / Area'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Search for routes and return them ordered by sequence.

        Args:
            name: Search term or display name supplied by the caller.
            domain: Odoo domain limiting the records considered by the operation.
            operator: Search operator requested by Odoo name-search APIs.
            limit: Maximum number of records to return.

        Returns:
            list: Matching record identifiers and display names in Odoo format.
        """
        search_domain = Domain([('name', operator, name)]) if name else Domain.TRUE
        if domain:
            search_domain = search_domain & Domain(domain)

        records = self.search(search_domain, limit=limit, order='sequence, name')
        return [(int(record.id), str(record.display_name)) for record in records]
