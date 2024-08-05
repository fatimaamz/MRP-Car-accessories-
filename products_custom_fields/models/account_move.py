from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    pcs = fields.Integer(string='PCS')
    weight = fields.Float(string='Poids')
    tracking = fields.Char(string='Suivi')
    custom_clearance = fields.Char(string='Dédouanement')
    transport = fields.Char(string='Transport')
    carrier = fields.Char(string='Transporteur')
