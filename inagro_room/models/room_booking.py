# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, _


class RoomBooking(models.Model):
    
    _name = "room.booking"
    _description = " List of Room Booked"
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = 'start_date desc, name'
    
    def _get_department(self):
        employees = self.env.user.employee_ids
        return (
            employees[0].department_id
            if employees
            else self.env["hr.department"] or False
        )    
        
    name = fields.Char("Ticket Booking Room", readonly=True)
    activities = fields.Text("Activities Name")
    room_id = fields.Many2one('master.room', "Room Name", track_visibility='onchange')
    partner_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user,
                                 index=True,
                                 required=True,
                                 states={'draft': [('readonly', False)]})
    
    department_id = fields.Many2one('hr.department', string='Department',
                                    store=True, readonly=True,required=True, default=_get_department)
    start_date = fields.Datetime("Start Time",track_visibility='onchange')
    finish_date = fields.Datetime("Finish Time",track_visibility='onchange')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')], 'State', required=True, default='draft', readonly=True, track_visibility='onchange')
        
    @api.constrains('start_date', 'finish_date')
    def check_time(self):
        for room_date in self:
            if room_date.start_date > room_date.finish_date:
                raise ValidationError(_('Your Start Time is more than Finish Date, please check the Times'))
    @api.multi
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('You cannot delete this data !!!'))
            return super(RoomBooking, self).unlink()
            
    @api.multi
    def set_to_cancel(self):
        self.state = 'cancel'
        return True
    
    @api.multi
    def set_to_confirm(self):
        vals = {}
        for reservation in self:
            reserv_checkin = reservation.start_date
            reserv_checkout = reservation.finish_date
            room_id = self.env['room.booking'].search([('state', '=', 'confirm'), ('room_id', '=', reservation.room_id.id)])
            if room_id:
                room_bool = False
                for reserv in room_id:
                    check_in = reserv.start_date
                    check_out = reserv.finish_date

                    # print(reserv.id,'reserv')
                    # print(reserv_checkin,'reserv_checkin')
                    # print(reserv_checkout,'reserv_checkout')
                    # print(check_in,'check_in')
                    # print(check_out,'check_out')

                    if check_in < reserv_checkin < check_out and int(reservation.id) != int(reserv.id):
                        room_bool = True
                        # print('1')
                        
                    if check_in < reserv_checkout < check_out and int(reservation.id) != int(reserv.id):
                        room_bool = True
                        # print('2')
                        
                    if reserv_checkin <= check_in and \
                            reserv_checkout >= check_out:
                        room_bool = True 
                        # print('3')

                    # print(room_bool,'room_bool')
                        
                    if room_bool:
                        raise ValidationError(_('You tried to Confirm '
                                                        'Booking with room '
                                                        'those already '
                                                        'reserved in this '
                                                        'booked period. '))


                    else:
                        # exit()
                        self.state = 'confirm'
            else:            
                self.state = 'confirm'

    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date:
            if datetime.strptime(str(self.start_date), DEFAULT_SERVER_DATETIME_FORMAT).date() < datetime.now().date():
                self.start_date = datetime.now()
    
    @api.onchange('finish_date')        
    def onchange_finish_date(self):
        if self.finish_date:
            if datetime.strptime(str(self.finish_date), DEFAULT_SERVER_DATETIME_FORMAT).date() < datetime.now().date():
                self.finish_date = datetime.now()
            
    @api.model
    def create(self, vals):
        if not vals:
            vals = {}
        vals['name'] = self.env['ir.sequence'].\
            next_by_code('room.booking') or '_New'
        return super(RoomBooking, self).create(vals)
    
