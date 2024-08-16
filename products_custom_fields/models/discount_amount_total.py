from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    converted_discounted_amount = fields.Monetary(string="Amount in CAD (75% Discount Applied)", currency_field='currency_id')

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.convert_and_apply_discount()
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        # Only apply discount if relevant fields are updated
        if 'amount_total' in vals or 'currency_id' in vals:
            self.convert_and_apply_discount()
        return result

    def convert_and_apply_discount(self):
        for order in self:
            # Only apply the discount if conditions are met
            if order.partner_id.country_id.code == 'US' and order.currency_id.name == 'USD':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')], limit=1)
                amount_usd = order.amount_total
                amount_cad = usd_currency._convert(amount_usd, cad_currency, order.company_id, fields.Date.today())
                discounted_amount = amount_cad * 0.75

                # Check if the calculated amount is different from the current amount
                if order.amount_total != discounted_amount:
                    
                    order.amount_total = discounted_amount
                    
                    order.converted_discounted_amount = discounted_amount
