from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    converted_discounted_amount = fields.Monetary(string="Amount in CAD (75% Discount Applied)", currency_field='currency_id')

    _recursion_guard = False

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.convert_and_apply_discount()
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        if not self._recursion_guard:
            self.convert_and_apply_discount()
        return result

    def convert_and_apply_discount(self):
        if self._recursion_guard:
            return
      
        self._recursion_guard = True
        
        for order in self:
            if order.partner_id.country_id.code == 'US' and order.currency_id.name == 'USD':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')], limit=1)
                amount_usd = order.amount_total
                amount_cad = usd_currency._convert(amount_usd, cad_currency, order.company_id, fields.Date.today())
                discounted_amount = amount_cad * 0.75
                
                # Update amount_total directly
                order.write({'amount_total': discounted_amount})
                
                # Update the converted discounted amount field
                order.converted_discounted_amount = discounted_amount

        # Reset the flag
        self._recursion_guard = False
