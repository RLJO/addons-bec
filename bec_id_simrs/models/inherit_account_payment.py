# -*- coding: utf-8 -*-

from odoo import models, fields, api

class bec_account_payment(models.Model):
    _inherit = "account.payment"

    id_simrs = fields.Integer(string='Id DP SIMRS')


class bec_AccountInvoice(models.Model):
    _inherit = "account.invoice"

    id_simrs = fields.Integer(string='Id Invoice SIMRS')

class bec_Partner(models.Model):
    _inherit = "res.partner"

    id_simrs = fields.Integer(string='Id Customer SIMRS')

class bec_AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    id_simrs = fields.Integer(string='Id refund dp SIMRS')