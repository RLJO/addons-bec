# -*- coding: utf-8 -*-
{
    'name': "Inagro Room",

    'summary': """
        faliqul.fikri@inagro.co.id""",

    'description': """
        Aplikasi Penggunaan Room untuk kebutuhan internal Inagro
    """,

    'author': "INAGRO",
    'website': "https://www.inagro.co.id/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'license': 'AGPL-3',

    # any module necessary for this one to work correctly
    # 'images': ['static/description/logo.jpg'],
    'depends': ['web','mail'],

    # always loaded
    'data': [
#         'views/assets.xml',
        'data/res_groups.xml',
        'security/ir.model.access.csv',
        'views/menus.xml',
        'data/room_booking_sequence.xml',
        'views/master_room_views.xml',
        'views/room_booking_views.xml',
        
        
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
    'images': ['static/description/Hotel.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}