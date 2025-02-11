# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'POS API Integration',
    'version': '16.0.1.0',
    'category': 'Point of Sale',
    'summary': 'Integration with external APIs for the Point of Sale application',
    'description': """
        This module integrates the Point of Sale application with various external APIs.
        - Feature 1: Backup order details.
    """,
    'author': 'ULTS',
    'website': 'https://ultsglobal.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        "point_of_sale.assets": [
            "pos_api_integration/static/src/js/**/*.js",
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
