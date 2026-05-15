# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Flights res config settings module.

Purpose:
    Defines classes ResConfigSettings for daily operations boards, simulator operations, flight execution logs, cancellation workflows, schedule imports, and hour distribution.

External Dependencies:
    Odoo ORM APIs from ``odoo.api``, ``odoo.fields``, and
    ``odoo.models`` are used throughout the addon.

Related Modules:
    Depends on: fs_scheduling, fs_fleet, fs_training, fs_people, mail, bus.
    fs_scheduling provides planned flights.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight operations module.

    This class is part of the Flight School Management Odoo addon suite.
    It uses the Odoo ORM for persistence, security, and view integration.

    Attributes:
        _inherit: Odoo model(s) extended by this class: ``res.config.settings``.

    Related:
        fs_scheduling provides planned flights.
        fs_training enrollments receive completed-hour updates.
    """

    _inherit = 'res.config.settings'

    # === Operations Board Settings ===
    fs_operations_page_size = fields.Integer(
        string='Flights per Page',
        default=10,
        config_parameter='flight_school.operations_page_size',
        help="Number of flights to display per page on the Operations Board carousel.",
    )
    fs_operations_carousel_interval = fields.Integer(
        string='Carousel Interval (seconds)',
        default=10,
        config_parameter='flight_school.operations_carousel_interval',
        help="Seconds to wait before auto-advancing to the next page (0 to disable).",
    )

    @api.constrains('fs_operations_page_size', 'fs_operations_carousel_interval')
    def _check_operations_board_settings(self):
        """Validate operations board settings business rules.

        Returns:
            None: Updates Odoo records, computed fields, or wizard state in place.

        Raises:
            ValidationError: If record data violates a model constraint.
        """
        for rec in self:
            if rec.fs_operations_page_size <= 0:
                raise ValidationError('Flights per Page must be greater than 0.')
            if rec.fs_operations_carousel_interval < 0:
                raise ValidationError('Carousel Interval must be 0 or a positive number.')
