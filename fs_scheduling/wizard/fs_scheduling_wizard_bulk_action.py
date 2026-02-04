# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class FsSchedulingWizardBulkAction(models.TransientModel):
    """Wizard for bulk actions on scheduling wizard lines."""

    _name = 'fs.scheduling.wizard.bulk.action'
    _description = 'Scheduling Wizard Bulk Action'

    wizard_id = fields.Many2one(
        'fs.scheduling.wizard',
        string='Scheduling Wizard',
        required=True,
        ondelete='cascade',
    )
    
    action_type = fields.Selection([
        ('route', 'Assign Route'),
        ('aircraft_type', 'Assign Aircraft Type'),
        ('add_mission', 'Mark as ADD Mission'),
    ], string='Action Type', required=True)
    
    line_count = fields.Integer(string='Lines to Update', readonly=True)
    
    # Route assignment fields
    route_id = fields.Many2one(
        'fs.flight.route',
        string='Route / Area',
        help="Route to assign to selected lines.",
    )
    apply_to_lines_without_route = fields.Boolean(
        string='Only Lines Without Route',
        default=True,
        help="If checked, only lines without a route will be updated.",
    )
    
    # Aircraft type assignment fields
    aircraft_type_id = fields.Many2one(
        'fs.aircraft.type',
        string='Aircraft Type',
        help="Aircraft type to add to selected lines.",
    )
    replace_existing = fields.Boolean(
        string='Replace Existing Types',
        default=False,
        help="If checked, replaces existing aircraft types. Otherwise, adds to existing.",
    )
    
    # ADD mission fields
    mark_all_as_add = fields.Boolean(
        string='Mark All as ADD',
        default=True,
        help="Mark all eligible lines as ADD missions.",
    )
    
    # UI helper
    display_name = fields.Char(compute='_compute_display_name')
    
    @api.depends('action_type')
    def _compute_display_name(self):
        action_labels = {
            'route': 'Bulk Assign Route',
            'aircraft_type': 'Bulk Assign Aircraft Type',
            'add_mission': 'Bulk Mark as ADD',
        }
        for rec in self:
            action_key = rec.action_type or 'route'  # Default to route if not set
            rec.display_name = action_labels.get(action_key, 'Bulk Action')

    def action_apply(self):
        """Apply the bulk action to the wizard lines."""
        self.ensure_one()
        
        if self.action_type == 'route':
            return self._apply_route_assignment()
        elif self.action_type == 'aircraft_type':
            return self._apply_aircraft_type_assignment()
        elif self.action_type == 'add_mission':
            return self._apply_add_mission()
        
        raise UserError(_("Unknown action type."))

    def _apply_route_assignment(self):
        """Assign route to wizard lines."""
        if not self.route_id:
            raise UserError(_("Please select a route to assign."))
        
        wizard = self.wizard_id
        if self.apply_to_lines_without_route:
            lines = wizard.line_ids.filtered(lambda l: not l.route_id and not l.is_sim)  # type: ignore
        else:
            lines = wizard.line_ids.filtered(lambda l: not l.is_sim)  # type: ignore
        
        if not lines:
            raise UserError(_("No lines to update."))
        
        updated_count = 0
        for line in lines:
            line.route_id = self.route_id  # type: ignore
            updated_count += 1
        
        _logger.info(
            "Bulk route assignment: %d lines updated with route '%s'",
            updated_count, self.route_id.name  # type: ignore
        )
        
        return wizard._reopen_wizard()  # type: ignore

    def _apply_aircraft_type_assignment(self):
        """Assign aircraft type to wizard lines."""
        if not self.aircraft_type_id:
            raise UserError(_("Please select an aircraft type to assign."))
        
        wizard = self.wizard_id
        lines = wizard.line_ids  # type: ignore
        
        if not lines:
            raise UserError(_("No lines to update."))
        
        updated_count = 0
        for line in lines:
            if self.replace_existing:
                line.aircraft_type_ids = [(6, 0, [self.aircraft_type_id.id])]  # type: ignore
            else:
                # Add to existing types
                current_ids = line.aircraft_type_ids.ids  # type: ignore
                if self.aircraft_type_id.id not in current_ids:
                    current_ids.append(self.aircraft_type_id.id)
                    line.aircraft_type_ids = [(6, 0, current_ids)]  # type: ignore
            updated_count += 1
        
        _logger.info(
            "Bulk aircraft type assignment: %d lines updated with type '%s'",
            updated_count, self.aircraft_type_id.name  # type: ignore
        )
        
        return wizard._reopen_wizard()  # type: ignore

    def _apply_add_mission(self):
        """Mark lines as ADD missions (excludes SIM sessions)."""
        wizard = self.wizard_id
        # Exclude SIM sessions - they don't use ADD concept
        lines = wizard.line_ids.filtered(lambda l: not l.is_added_mission and not l.is_sim)  # type: ignore
        
        if not lines:
            raise UserError(_("No eligible flights to mark as ADD (SIM sessions excluded)."))
        
        updated_count = 0
        for line in lines:
            line.is_added_mission = True  # type: ignore
            updated_count += 1
        
        _logger.info(
            "Bulk ADD mission assignment: %d lines marked as ADD",
            updated_count
        )
        
        return wizard._reopen_wizard()  # type: ignore

    def action_cancel(self):
        """Cancel and return to the wizard."""
        return self.wizard_id._reopen_wizard()  # type: ignore
