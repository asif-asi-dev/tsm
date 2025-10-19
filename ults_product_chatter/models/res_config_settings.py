# -*- coding: utf-8 -*-
from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_tracking_mode = fields.Selection([
        ('specific', 'Track Specific Fields Only (12 predefined fields)'),
        ('all', 'Track All Fields (50+ fields automatically)'),
    ], string='Product Field Tracking', default='specific',
        config_parameter='ults_product_chatter.tracking_mode',
        help="Specific: Track only important fields (name, price, category, etc.)\n"
             "All: Track all product fields automatically (complete audit trail)")
