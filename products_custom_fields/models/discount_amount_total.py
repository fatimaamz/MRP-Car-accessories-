from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    discounted_amount_total = fields.Monetary(string='Discounted Amount Total', compute='_compute_discounted_amount_total', store=True)

    @api.depends('price_total', 'order_id.partner_id')
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
                    else:
                        _logger.warning("No rate record found.")
                    
                    inverse_rate = rate_record.inverse_company_rate
                    total_cad = order.price_subtotal * inverse_rate
                    discounted_total = total_cad * 0.75
                    order.discounted_amount_total = discounted_total
                   
                else:
                    _logger.warning("USD currency not found.")
            else:
                order.discounted_amount_total = 0

    
            
    @api.model
    def create(self, vals):
        line = super(SaleOrderLine, self).create(vals)
        if not self.env.context.get('skip_price_update', False):
            context = dict(self.env.context, skip_price_update=True)
            line.with_context(context)._compute_discounted_amount_total()
            line.with_context(context).write({'price_subtotal': line.discounted_amount_total})

        return line

    def write(self, vals):
        if not self.env.context.get('skip_price_update', False):
            res = super(SaleOrderLine, self).write(vals)
            for line in self:
                context = dict(self.env.context, skip_price_update=True)
                line.with_context(context)._compute_discounted_amount_total()
                line.with_context(context).write({'price_subtotal': line.discounted_amount_total})
            return res
        else:
            return super(SaleOrderLine, self).write(vals)
       
