# -*- coding: utf-8 -*-
import re

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import africastalking


class Africastalking(models.Model):
    _name = 'odoo.africastalking'
    _inherit = ["mail.thread", ]
    _description = 'Odoo Africastalking'

    def _get_default_username(self):
        """ Get the default app user name set in the company"""
        username = self.env.user.company_id.app_user
        return username

    def _get_default_api_key(self):
        """ Get the default app Api key set in the company"""
        key = self.env.user.company_id.api_key
        return key

    app_name = fields.Char('App username', default=_get_default_username)
    api_key = fields.Char('API key', default=_get_default_api_key)

    def _intitalize_africastalking(self, user_name, api_token):
        africastalking.initialize(
            user_name, api_token)

    def _initalize_sandbox(self, ):
        africastalking.initialize(
            "sandbox", "bdc7af624404fe128411a9244ffc38494a32dc52fc89435819540d16ddfaf121")

    name = fields.Char('Name')
    partner_id = fields.Many2one("res.partner", string="Partner", tracking=True)
    contact = fields.Char('Contact', compute="_compute_partner_phone",
                          help="Contact format(+25612345,2567123456,0712345678,7123456789")
    message = fields.Text('Message')
    response_message = fields.Text('Response', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent'), ('fail', 'fail')], default="draft", string="Status",
                             tracking=True)
    date_send = fields.Datetime("Time Sent", tracking=True)
    balance = fields.Char("Balance Remaining", tracking=True)
    phone_no = fields.Char("Phone Number", tracking=True, placeholder="+256000000")

    def fetch_amount(self):
        """Get the remaining balance"""
        self._intitalize_africastalking(self.app_name, self.api_key)
        application = africastalking.Application
        res = application.fetch_application_data()
        # self.message_post(body=res)
        self.balance = res['UserData']['balance']

    def set_contact(self, phone):
        if phone:
            if not bool(re.fullmatch(r'^\+?[0-9]+$', phone)) and self.state == 'draft':
                self.phone_no = False
                # raise UserError(f"The phone {phone} must be in digits only!")

            if phone.startswith('+256') and len(phone) == 13:
                return str(phone)
            elif phone.startswith('0') and len(phone) == 10:
                return str('+256' + str(phone[1:]))
            elif phone.startswith('7') and len(phone) == 9:
                return "+256" + phone
            elif phone.startswith('256') and len(phone) == 12:
                return '+' + phone
            else:
                return False

    @api.depends('partner_id', 'phone_no')
    @api.onchange('phone_no', 'partner_id')
    def _compute_partner_phone(self):
        for rec in self:
            if rec.partner_id:
                text_no = rec.partner_id.phone if rec.partner_id.phone else rec.partner_id.mobile
                text_no = text_no.replace(' ', '')
                rec.contact = rec.set_contact(text_no)
                if not rec.contact and rec.phone_no:
                    text_no = rec.phone_no
                    rec.contact = rec.set_contact(text_no)  # substitute for only run phone
            elif rec.phone_no:
                text_no = rec.phone_no
                text_no = text_no.replace(' ', '')
                rec.contact = rec.get_contact(text_no)
            else:
                rec.contact = False

    def send_sms(self, msg, recipients):
        """ Method for sending the sms
        The msg is a parameter passed which is a string
        The receiptients is an array of receiptients to tbe passed
        """
        if len(recipients) < 1:
            raise models.ValidationError("Please add a contact to send an sms")
        self._intitalize_africastalking(self._get_default_username(), self._get_default_api_key())
        sms = africastalking.SMS
        response = sms.send(msg, recipients)
        return response

    def send_msg_sandbox(self, msg, recipients):
        if len(recipients) < 1:
            raise models.ValidationError("Please add a contact to send an sms")
        self._initalize_sandbox()
        sms = africastalking.SMS
        response = sms.send(msg, recipients)
        return response

    def action_send_sandbox(self):
        response = self.send_msg_sandbox(self.message, [str(self.contact)])
        self.response_message = response['SMSMessageData']['Message']
        if response['SMSMessageData']['Recipients'][0]['status'] == 'Success':
            self.write({
                'state': 'sent',
                'date_send': datetime.now()
            })
        else:
            self.write({
                'state': 'fail',
                'date_send': datetime.now(),
            })

    def action_sending(self):
        """ send the sms"""
        if self.contact:
            response = self.send_sms(self.message, [str(self.contact)])
            self.response_message = response['SMSMessageData']['Message']
            if response['SMSMessageData']['Recipients'][0]['status'] == 'Success':
                self.write({
                    'state': 'sent',
                    'date_send': datetime.now()
                })
            else:
                self.write({
                    'state': 'fail',
                    'date_send': datetime.now(),
                })
        else:
            raise UserError("No contact number is set below! \nPlease enter a phone number or set a partner\'s "
                            "contact number.")
            # raise models.ValidationError('Message not sent because of the following reason'+ response['SMSMessageData']['Message'])

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('odoo.africastalking') or _('New')
        return super(Africastalking, self).create(vals)


class Company(models.Model):
    _inherit = "res.company"

    app_user = fields.Char("AfricaStalking App Username")
    api_key = fields.Char("Africastalking API key")


class Wizard(models.TransientModel):
    _name = "odoo.africastalking.wizard"
    _description = "Odoo Africastalking Sms Wizard"

    partner_id = fields.Many2one('res.partner', string="Partner")
    contact = fields.Char('Contact', compute="_compute_partner_phone")
    message = fields.Text('Message')
    response_message = fields.Text('Response')
    balance = fields.Char("Balance Remaining", )

    @api.depends('partner_id')
    def _compute_partner_phone(self):
        for rec in self:
            if rec.partner_id.phone or rec.partner_id.mobile:
                text = rec.partner_id.phone if rec.partner_id.phone else rec.partner_id.mobile
                text = text.replace(' ', '')
                if text:
                    if text.startswith('+256') and len(text) == 13:
                        rec.contact = (str(text))
                    elif text.startswith('0') and len(text) == 10:
                        rec.contact = str('+256' + str(text[1:]))
                    elif text.startswith('7') and len(text) == 9:
                        rec.contact = "+256" + text
                    elif text.startswith('256') and len(text) == 12:
                        rec.contact = '+' + text
                    else:
                        rec.contact = False
                        # raise ValidationError('The contact number of the Selected Partner is not right..')
                else:
                    rec.contact = False
            else:
                rec.contact = False

    balance = fields.Char("Balance Remaining", )

    def action_sending(self):
        for rec in self:
            if not rec.contact:
                raise UserError('Phone number missing for the Customer')
            # Set your shortCode or senderId
            sender = "98512"
            vals = {
                'message': rec.message,
                'partner_id': rec.partner_id.id,
                'contact': rec.contact,
                'date_send': datetime.now()

            }
            sms_obj = self.env['odoo.africastalking'].create(vals)
            sms_obj.fetch_amount()
            sms_obj.action_sending()
