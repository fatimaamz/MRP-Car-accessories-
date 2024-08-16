from odoo import models, fields, api
from datetime import date

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    adjusted_amount_total = fields.Monetary(
        string="Adjusted Amount Total", 
        currency_field='currency_id'
    )

    @api.depends('partner_id', 'amount_total')
    def convert_and_apply_discount(self):
        for order in self:
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')], limit=1)

                if not usd_currency or not cad_currency:
                    continue  

                today = date.today()
                rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)

                if rate_record:
                    inverse_rate = rate_record.inverse_company_rate

                    # Convertir le montant total en CAD et appliquer la remise de 75%
                    amount_usd = order.amount_total
                    amount_cad = amount_usd * inverse_rate
                    discounted_amount = amount_cad * 0.75

                    # Mettre à jour amount_total avec le montant remisé
                    order.write({'amount_total': discounted_amount})
                    
                    order.adjusted_amount_total = discounted_amount
                else:
                    order.adjusted_amount_total = order.amount_total
            else:
                order.adjusted_amount_total = order.amount_total

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.convert_and_apply_discount()
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        if not self.env.context.get('skip_discount_update', False):
            self.convert_and_apply_discount()
        return result
