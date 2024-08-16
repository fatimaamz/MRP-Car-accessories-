from odoo import models, fields, api
from datetime import date

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_total', 'partner_id')
    def _compute_custom_total(self):
        for order in self:
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                cad_currency = self.env['res.currency'].search([('name', '=', 'CAD')], limit=1)

                if usd_currency and cad_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)
                    
                    if rate_record:
                        inverse_rate = rate_record.inverse_company_rate
                        total_cad = order.amount_total * inverse_rate
                        discounted_total = total_cad * 0.75
                        
                        # Use context to avoid recursion
                        context = dict(self.env.context, skip_custom_total=True)
                        order.with_context(context).write({'amount_total': discounted_total})

    def write(self, vals):
        # Bypass infinite recursion using context
        if not self.env.context.get('skip_custom_total'):
            self._compute_custom_total()
        return super(SaleOrder, self).write(vals)

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order._compute_custom_total()
        return order
