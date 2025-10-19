# -*- coding: utf-8 -*-
{
    'name': 'ULTS Product Field Tracking',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Track product field changes in chatter with configurable modes',
    'description': """
Product Field Tracking
======================

Track all product field changes automatically and display them in the chatter.

Features:
---------
* Automatic field change tracking
* Configurable tracking modes (specific fields or all fields)
* Detailed change history with before/after values
* Full audit trail with user and timestamp
* Support for all field types (text, numbers, relations, etc.)
* Professional Odoo-style formatting

Configuration:
--------------
Settings > Inventory > Operations > Product Field Tracking
- Specific Mode: Track 12 predefined important fields
- All Mode: Track 50+ fields automatically (excludes system fields)
    """,
    'author': 'ULTS',
    'website': 'https://www.ultsglobal.com',
    'depends': [
        'product',
        'mail',
        'stock',
    ],
    'data': [
        # 'views/product_template_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [
        'demo/product_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
