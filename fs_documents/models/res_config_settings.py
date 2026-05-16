# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

"""Flight School Documents settings hooks."""

from odoo import models


class ResConfigSettings(models.TransientModel):
    """Refresh document statuses when shared Flight School settings change."""

    _inherit = 'res.config.settings'

    def set_values(self):
        """Persist settings and refresh stored document expiry statuses.

        Document expiry warning windows reuse the related field settings from
        `fs_people`, such as medical, license, English, insurance, and security
        clearance warning days.
        """
        result = super().set_values()
        self.env['fs.document'].cron_refresh_expiry_status()
        return result
