from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    converted_discounted_amount = fields.Monetary(string="Amount in CAD (75% Discount Applied)", currency_field='currency_id')

    @api.depends('partner_id','amount_total')
    def convert_and_apply_discount(self):
        # Use context to prevent recursion
        context = dict(self.env.context, skip_discount_update=True)
        for order in self:
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')], limit=1)

                if not usd_currency or not cad_currency:
                    continue  

                amount_usd = order.amount_total
                amount_cad = usd_currency._convert(amount_usd, cad_currency, order.company_id, fields.Date.today())
                discounted_amount = amount_cad * 0.75

                if order.amount_total != discounted_amount:
                    order.with_context(context).write({'amount_total': discounted_amount})

                order.with_context(context).converted_discounted_amount = discounted_amount

    
    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order.convert_and_apply_discount()
        return order

    def write(self, vals):
        if not self.env.context.get('skip_discount_update', False):
            result = super(SaleOrder, self).write(vals)
            self.convert_and_apply_discount()
            return result
        return super(SaleOrder, self).write(vals)

    
