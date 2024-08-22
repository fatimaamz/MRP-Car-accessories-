from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discounted_amount_total = fields.Monetary(string='Discounted Amount Total', compute='_compute_discounted_amount_total', store=True)

    @api.depends('order_line.price_total', 'partner_id')
    def _compute_discounted_amount_total(self):
        for order in self:
            if order.order_id.partner_id.country_id.code == 'US':
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

                if usd_currency:
                    today = date.today()
                    rate_record = usd_currency.rate_ids.filtered(lambda r: r.name == today)

                    # If no rate for today, take the last available rate
                    if not rate_record:
                        rate_record = usd_currency.rate_ids.sorted(key=lambda r: r.name, reverse=True)[:1]
                    
                    inverse_rate = rate_record.inverse_company_rate
                    total_cad = order.price_subtotal * inverse_rate
                    discounted_total = total_cad * 0.75
                    order.discounted_amount_total = discounted_total
                    else:
                        _logger.warning("No rate record found.")
                else:
                    _logger.warning("USD currency not found.")
            else:
                order.discounted_amount_total = 0

    
            
    @api.model
    def create(self, vals):
        order = super(SaleOrderLine, self).create(vals)

        if order:
            context = dict(self.env.context, skip_update_amount_total=True)
            order.with_context(context)._compute_discounted_amount_total()
            order.with_context(context).write({'price_subtotal': order.discounted_amount_total})

        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for order in self:
            order._compute_discounted_amount_total()
            order.write({'price_subtotal': line.discounted_amount_total})

        return res
       
