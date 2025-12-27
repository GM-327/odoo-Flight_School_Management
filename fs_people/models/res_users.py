# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to link the new user back to the personnel record if specified in context."""
        users = super(ResUsers, self).create(vals_list)
        
        # Check context for personnel linkage
        person_id = self.env.context.get('fs_person_id')
        person_model = self.env.context.get('fs_person_model')
        
        if person_id and person_model:
            # Logic for multiple users created at once (unlikely in this context but good practice)
            # Use the first user if person_id is provided
            person_rec = self.env[person_model].browse(person_id)
            if person_rec.exists() and not person_rec.user_id:
                person_rec.write({'user_id': users[0].id})
                
        return users
