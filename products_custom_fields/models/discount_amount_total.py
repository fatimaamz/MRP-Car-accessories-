from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.price_subtotal', 'order_line.price_tax', 'order_line.price_total')
    def _compute_amounts(self):
       
        # Prevent recursion by using a context flag
        if self.env.context.get('skip_discount_calculation', False):
            return

        # Call the original method to perform the default behavior
        super(SaleOrder, self)._compute_amounts()

        for order in self:
            # If the customer is from the USA, apply the discount
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)

                    # If no rate for today, take the last available rate
                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]
                    else:
                        _logger.warning("No rate record found.")
                
                if usd_currency:
                    # Convert the total amount to USD using Odoo's currency conversion
                    amount_total_in_usd = order.currency_id._convert(
                        order.amount_total,  # Use the computed amount_total from the original method
                        usd_currency,
                        order.company_id,
                        order.date_order or fields.Date.today()
                    )

                    # Apply 75% discount to the total amount in USD
                    discounted_total_in_usd = amount_total_in_usd * 0.75

                    # Convert the discounted total back to the company's currency (e.g., CAD)
                    discounted_total_in_company_currency = usd_currency._convert(
                        discounted_total_in_usd,
                        order.currency_id,
                        order.company_id,
                        order.date_order or fields.Date.today()
                    )

                    # Avoid recursion by setting the context flag
                    context = dict(self.env.context, skip_discount_calculation=True)

                    # Override the amount_total with the discounted total (using context to avoid recursion)
                    order.with_context(context).amount_total = discounted_total_in_company_currency
                else:
                    _logger.warning("USD currency not found. No discount applied.")
