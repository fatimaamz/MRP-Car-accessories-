from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('amount_total','partner_id')
    def convert_and_apply_discount(self):
        for order in self:
            if order.partner_id.country_id.code == 'US' :
               
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')], limit=1)

                # Convertir le montant total de la commande en CAD
                amount_usd = order.amount_total
                amount_cad = usd_currency._convert(amount_usd, cad_currency, order.company_id, fields.Date.today())

                # Appliquer la remise de 75 %
                discounted_amount = amount_cad * 0.75


                order.update({
                    'amount_total': discounted_amount,  
                })
    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.convert_and_apply_discount()
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        self.convert_and_apply_discount()
        return result

               
