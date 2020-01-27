# -*- coding: utf-8 -*-

import time
import math
import re

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

class bec_tax_AccountTax(models.Model):
    _inherit = 'account.tax'

    dpp = fields.Boolean(default=False,string='By Dpp?')
    parent_dpp_id = fields.Many2one('account.tax', string='Dpp Parent')

    @api.onchange('dpp')
    def _domain_dpp(self):
        res = {}
        res['domain']={'parent_dpp_id':[('type_tax_use', '=', self.type_tax_use)]}
        return res

    # def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
    #     """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
    #         price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
    #     """

    #     # print(self.amount,'amount')
    #     # print(base_amount, ' base_amount')
    #     # print(price_unit, ' price_unit')
    #     # print(quantity, ' quantity')
    #     # print(price_subtotal, ' price_subtotal')


    #     self.ensure_one()
    #     if self.amount_type == 'fixed':
    #         if base_amount:
    #             return math.copysign(quantity, base_amount) * self.amount
    #         else:
    #             return quantity * self.amount

    #     price_include = self.price_include or self._context.get('force_price_include')

    #     if (self.amount_type == 'percent' and not price_include) or (self.amount_type == 'division' and price_include):
    #         # return base_amount * self.amount / 100
    #         print('satu')
    #         final_amount = base_amount * self.amount / 100
    #     if self.amount_type == 'percent' and price_include:
    #         # return base_amount - (base_amount / (1 + self.amount / 100))
    #         print('dua')
    #         print(self.amount,' self.amount')
    #         final_amount = base_amount - (base_amount / (1 + self.amount / 100))
    #         print(base_amount,' - (',base_amount,' / (1 +', self.amount,' / 100))')
    #     if self.amount_type == 'division' and not price_include:
    #         # return base_amount / (1 - self.amount / 100) - base_amount
    #         print('tiga')
    #         final_amount = base_amount / (1 - self.amount / 100) - base_amount
    #     print(final_amount,' final_amount')
    #     # exit()
    #     return final_amount


    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        # print('===============================================================================================')
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id
        taxes = []
        prec = currency.decimal_places

        round_tax = False if company_id.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])

        if not round_tax:
            prec += 5

        base_values = self.env.context.get('base_values')
        if not base_values:
            total_excluded = total_included = base = round(price_unit * quantity, prec)
        else:
            total_excluded, total_included, base = base_values

        for tax in self.sorted(key=lambda r: r.sequence):
            price_include = self._context.get('force_price_include', tax.price_include)

            if tax.amount_type == 'group':
                children = tax.children_tax_ids.with_context(base_values=(total_excluded, total_included, base))
                ret = children.compute_all(price_unit, currency, quantity, product, partner)
                total_excluded = ret['total_excluded']
                base = ret['base'] if tax.include_base_amount else base
                total_included = ret['total_included']
                tax_amount = total_included - total_excluded
                taxes += ret['taxes']
                continue

            # print('---------------------------------------------------------------------------------------')
            # print(len(tax.parent_dpp_id),' ggg')
            if tax.dpp == True and len(tax.parent_dpp_id) > 0:
            	print('dpp')
            	tax_awal = tax.parent_dpp_id._compute_amount(base, price_unit, quantity, product, partner)
            	price_unit = price_unit - tax_awal
            	base = base - tax_awal
            	tax_amount = base * (tax.amount/100)
            else:
            	tax_amount = tax._compute_amount(base, price_unit, quantity, product, partner)

            
            if not round_tax:
                tax_amount = round(tax_amount, prec)
            else:
                tax_amount = currency.round(tax_amount)

            if price_include:
                total_excluded -= tax_amount
                base -= tax_amount
            else:
                total_included += tax_amount

            # Keep base amount used for the current tax
            tax_base = base

            if tax.include_base_amount:
                base += tax_amount

            taxes.append({
                'id': tax.id,
                'name': tax.with_context(**{'lang': partner.lang} if partner else {}).name,
                'amount': tax_amount,
                'base': tax_base,
                'sequence': tax.sequence,
                'account_id': tax.account_id.id,
                'refund_account_id': tax.refund_account_id.id,
                'analytic': tax.analytic,
                'price_include': tax.price_include,
                'tax_exigibility': tax.tax_exigibility,
            })

        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': currency.round(total_excluded) if round_total else total_excluded,
            'total_included': currency.round(total_included) if round_total else total_included,
            'base': base,
        }
    
    

    
