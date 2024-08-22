from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    def _compute_amounts(self):
        if self.env.context.get('skip_discount_calculation', False):
            return

        super(SaleOrder, self)._compute_amounts()

        for order in self:
            # If the customer is from the USA, apply the discount
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)

                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]
                    
                 
                    inverse_rate = rate_record.inverse_company_rate
                    amount_total_in_usd = orde.amount_total * inverse_rate
                    discounted_total_in_usd = amount_total_in_usd * 0.75
                    context = dict(self.env.context, skip_discount_calculation=True)

                    order.with_context(context).amount_total = discounted_total_in_usd 
                
