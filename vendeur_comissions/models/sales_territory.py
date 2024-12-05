from odoo import models, fields



class SalesTerritory(models.Model):
    _name = 'sales.territory'
    _description = 'Sales Territory'

    name = fields.Char(string="Territory Name", required=True)
    weekly_target = fields.Float(string="Weekly Target", required=True)
    representative_ids = fields.Many2many(
        'res.users', string="Assigned Representatives"
    )
    #name = fields.Char(string="Nom du Territoire", required=True)
    #objectif_hebdomadaire = fields.Float(string="Objectif Hebdomadaire ($)", required=True)


class SalesCommission(models.Model):
    _name = 'sales.commission'
    _description = 'Sales Commission'

    user_id = fields.Many2one('res.users', string="Representative", required=True)
    invoice_id = fields.Many2one('account.move', string="Invoice", required=True)
    commission_amount = fields.Float(string="Commission Amount", required=True)
    commission_date = fields.Date(string="Commission Date", default=fields.Date.today)


 


