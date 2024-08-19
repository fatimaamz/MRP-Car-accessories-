from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discounted_amount_total = fields.Monetary(string='Discounted Amount Total', compute='_compute_discounted_amount_total', store=True)

    @api.depends('order_line.price_total', 'partner_id')
    def _compute_discounted_amount_total(self):
        for order in self:
            if order.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)

                    # If no rate for today, take the last available rate
                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]

                    _logger.info(f"Rate Record: {rate_record}")

                    if rate_record:
                        inverse_rate = rate_record.inverse_company_rate
                        _logger.info(f"Inverse Rate: {inverse_rate}")

                        total_cad = order.amount_total * inverse_rate
                        _logger.info(f"Total CAD: {total_cad}")

                        discounted_total = total_cad * 0.75
                        _logger.info(f"Discounted Total: {discounted_total}")

                        order.discounted_amount_total = discounted_total
                    else:
                        _logger.warning("No rate record found.")
                else:
                    _logger.warning("USD currency not found.")
            else:
                order.discounted_amount_total = 0

    
            
    @api.model
    def create(self, vals):
        # Create the record using the super method
        order = super(SaleOrder, self).create(vals)

        # After the record is created, compute and update the amount_total
        if order:
            order._compute_discounted_amount_total()
            order.update({'amount_total': order.discounted_amount_total})
        
        return order

    def write(self, vals):
        # Call the super method to perform the usual write operation
        res = super(SaleOrder, self).write(vals)

        # Update the amount_total after the record has been updated
        if 'amount_total' not in vals:
            for order in self:
                order._compute_discounted_amount_total()
                order.update({'amount_total': order.discounted_amount_total})

        return res
