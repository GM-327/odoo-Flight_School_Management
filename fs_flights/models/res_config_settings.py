# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration settings for flight operations module."""

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
