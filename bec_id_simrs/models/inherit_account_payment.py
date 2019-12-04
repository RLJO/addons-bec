# -*- coding: utf-8 -*-

from odoo import models, fields, api

class bec_account_payment(models.Model):
    _inherit = "account.payment"

    id_simrs = fields.Char(string='Id DP SIMRS')


class bec_AccountInvoice(models.Model):
    _inherit = "account.invoice"

    id_simrs = fields.Char(string='Id Invoice SIMRS')
    kd_t_simrs = fields.Char(string='Kode T SIMRS')
    no_inv_simrs = fields.Char(string='No Invoice SIMRS')
    no_tagihan_simrs = fields.Char(string='No Tagihan SIMRS')

class bec_Partner(models.Model):
    _inherit = "res.partner"

    id_simrs = fields.Char(string='Id Customer SIMRS')

class bec_AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    id_simrs = fields.Char(string='Id refund dp SIMRS')

class bec_product(models.Model):
    _inherit = "product.product"

    id_simrs = fields.Char(string='Id product SIMRS')

class bec_account_account(models.Model):
    _inherit = "account.account"

    id_simrs = fields.Char(string='Id COA SIMRS')