# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Restrict Out of Stock Product on POS',
    'version': '16.0.0.4',
    'category': 'Point of Sale',
    'summary': 'Out of stock product restriction on point of sales order restriction for out of stock product restriction for POS Restrict Out Stock Product POS stop out of stock product for POS available products only out of stock product alerts out of stock products POS',
    'description': """

        Restrict Out of Stock Product on POS in odoo,
        Display Product Stock in odoo,
        Stock Configuration on POS in odoo,
        Restrict Product Out of Stock in POS in odoo,
        Raise Warning Popup in odoo,
        Total On Hand Quantity of Product in odoo,

    """,
    'author': 'BrowseInfo',
    "price": 12,
    "currency": 'EUR',
    'website': 'https://www.browseinfo.com',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'bi_pos_restrict_stock/static/src/css/stock.css',
            'bi_pos_restrict_stock/static/src/js/Screens/ProductScreen.js',
            'bi_pos_restrict_stock/static/src/js/Screens/ProductWidget.js',
            'bi_pos_restrict_stock/static/src/js/Popups/BiWarningPopup.js',
            'bi_pos_restrict_stock/static/src/js/models.js',
            'bi_pos_restrict_stock/static/src/xml/Screens/ProductItem.xml',
            'bi_pos_restrict_stock/static/src/xml/Popups/BiWarningPopup.xml',
        ],
        
    },
    'license': 'OPL-1',
    'auto_install': False,
    'installable': True,
    'live_test_url':'https://youtu.be/h56RBaFf5Ww',
    'images':["static/description/Banner.gif"],
}

