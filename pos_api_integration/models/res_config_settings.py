# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_order_sync_api = fields.Char(related="pos_config_id.pos_order_sync_api", readonly=False)