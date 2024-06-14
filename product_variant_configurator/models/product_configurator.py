from odoo import models, fields

class SaleProductConfigurator(models.TransientModel):
    _inherit = 'sale.product.configurator'

    color_option = fields.Selection([
        ('paint_match', 'Paint Match'),
        ('carbon', 'Carbon'),
    ], string="Color Option", default='paint_match')

