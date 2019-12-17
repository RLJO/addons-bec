# -*- coding: utf-8 -*-

from odoo import models, fields, api

class bec_type_coa_simrs(models.Model):
    _name = "account.account_type_coa_simrs"
    _description = "Account type simrs"

    name = fields.Char(string='Account Type', required=True, translate=True)
    include_initial_balance = fields.Boolean(string="Bring Accounts Balance Forward")
    type = fields.Selection([
        ('other', 'Regular'),
        ('receivable', 'Receivable'),
        ('payable', 'Payable'),
        ('liquidity', 'Liquidity'),
    ], default='other')
    internal_group = fields.Selection([
        ('equity', 'Equity'),
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('income', 'Income'),
        ('expense', 'Expense'),
    ], string="Internal Group")
    note = fields.Text(string='Description')

class bec_type_coa_simrs_AccountAccount(models.Model):
    _inherit = "account.account"

    type_coa_simrs = fields.Many2one('account.account_type_coa_simrs', string='Type COA SIMRS', oldname="user_type",
        help="Type coa simrs")