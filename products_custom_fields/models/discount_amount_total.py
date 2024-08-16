from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

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

               
                order.write({'converted_discounted_amount': discounted_amount})

                order.update({
                    'amount_total': discounted_amount,  # Cela modifie le total de la commande
                })

               
