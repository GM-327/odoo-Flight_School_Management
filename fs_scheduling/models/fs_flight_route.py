# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models
from odoo.fields import Domain


class FsFlightRoute(models.Model):
    """Specific working areas or flight routes used for scheduling."""
    _name = 'fs.flight.route'
    _description = 'Flight Route / Area'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        """Search for routes and return them ordered by sequence."""
        search_domain = Domain([('name', operator, name)]) if name else Domain.TRUE
        if domain:
            search_domain = search_domain & Domain(domain)
        
        records = self.search(search_domain, limit=limit, order='sequence, name')
        return [(int(record.id), str(record.display_name)) for record in records]
