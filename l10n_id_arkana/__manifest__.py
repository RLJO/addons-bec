# -*- coding: utf-8 -*-
###################################################################################
#
#    Arkana Solusi Digital, PT
#    Copyright (C) 2018-TODAY Arkana Solusi Digital (<https://arkana.co.id>).
#    Author: Rachmat Aditiya (<https://arkana.co.id>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
{
    'name': 'Indonesian - Accounting',
    'version': '12.0.1.0.0',
    'category': 'Localization',
    'summary' : 'Chart of Account (COA) Indonesia',
    'description': """
This is the latest Indonesian Odoo localisation necessary to run Odoo accounting for SME's with:
=================================================================================================
    - Indonesian ready chart of account
    - tax structure
    - a few other adaptations""",
    'author': 'Arkana Solusi Digital',
    'maintainer': 'Arkana Solusi Digital',
    'company': 'Arkana Solusi Digital',
    'website': 'https://arkana.co.id',
    'depends': [ 'base', 'account','base_iban', 'base_vat', 'om_account_accountant'],
    'data': [
        'data/l10n_id_chart_data.xml',
        'data/account.account.template.csv',
        'data/account.chart.template.csv',
        'data/account.account.tag.csv',
        'data/account.tax.template.csv'
    ],
    'images': ['static/description/banner.jpeg'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
