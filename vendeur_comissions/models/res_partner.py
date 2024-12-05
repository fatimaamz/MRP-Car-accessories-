from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    territory_id = fields.Many2one(
        'sales.territory', string="Territoire",
        help="Affecter le client à un territoire de vente spécifique.")
  
#class ResUsers(models.Model):
    #_inherit = 'res.users'

    #days_worked = fields.Integer(string="Jours travaillés (cette semaine)", default=0)
