# -*- coding: utf-8 -*-

{
    "name": "Sale Register Payment",
    "version": "11.0",
    "category": "Sales",
    "author": "Preciseways",
    "website": "https://www.preciseways.com",
    "summary": """Allows full or partial payments from sales and this payment is linked with sales invoice in time of payment""",
    "description": """You can make partial or full payment from sale order and your partial payment is linked with this sales invoice when invoice is paid""",
    "depends": ["sale", "account"],
    "data": ["wizard/sale_advance_payment_wzd_view.xml",
             "views/sale_view.xml",
             ],
    "installable": True,
    "images":['static/description/banner.png'],
    'license': 'OPL-1',
}
