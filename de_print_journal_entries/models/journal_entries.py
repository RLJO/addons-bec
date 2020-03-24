# -*- coding: utf-8 -*-
from num2words import num2words
from odoo import models,api,fields

class PrintJournalEntries(models.Model):
    _inherit = 'account.move'

    # amount_to_text = fields.Char(string="Num Word", required=False, compute="amount_to_text" )

    def print_journal_entries(self):
        return self.env.ref('de_print_journal_entries.action_journal_entries_report').report_action(self)

    text_amount = fields.Char(string="NumWord", required=False, compute="amount_to_words" )
    @api.depends('amount')
    def amount_to_words(self):
        if self.company_id.text_amount_language_currency:
            self.text_amount = num2words(self.amount, to='currency',
                                         lang=self.company_id.text_amount_language_currency)
