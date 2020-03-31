# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class MasterRoom(models.Model):
    
    _name = "master.room"
    _description = " Room List"
    
    name = fields.Char('Room Name',required=True)
    initial = fields.Char('Initial Room',required=True)