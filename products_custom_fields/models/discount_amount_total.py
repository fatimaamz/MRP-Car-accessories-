from odoo import models, fields, api
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discounted_amount_total = fields.Monetary(string='Discounted Amount Total', compute='_compute_discounted_amount_total', store=True)
    discounted_amount_untaxed = fields.Monetary(string='Discounted Untaxed Amount', compute='_compute_discounted_amount_untaxed', store=True)

    @api.depends('order_line', 'partner_id')
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
                    
                    if rate_record:
                        inverse_rate = rate_record.inverse_company_rate
                        total_cad = order.amount_untaxed * inverse_rate
                        discounted_total = total_cad * 0.75
                        order.discounted_amount_total = discounted_total
                    else:
                        _logger.warning("No exchange rate record found for USD.")
                else:
                    _logger.warning("USD currency not found.")
            else:
                order.discounted_amount_total = 0

    @api.depends('discounted_amount_total', 'amount_untaxed')
    def _compute_discounted_amount_untaxed(self):
        for order in self:
            if order.partner_id.country_id.code == 'US':
                order.discounted_amount_untaxed = order.discounted_amount_total
            else:
                order.discounted_amount_untaxed = order.amount_untaxed

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if not self.env.context.get('skip_price_update', False):
            context = dict(self.env.context, skip_price_update=True)
            order.with_context(context)._compute_discounted_amount_total()
            order.with_context(context)._compute_discounted_amount_untaxed()

        return order

    def write(self, vals):
        if not self.env.context.get('skip_price_update', False):
            res = super(SaleOrder, self).write(vals)
            for order in self:
                context = dict(self.env.context, skip_price_update=True)
                order.with_context(context)._compute_discounted_amount_total()
                order.with_context(context)._compute_discounted_amount_untaxed()
            return res
        else:
            return super(SaleOrder, self).write(vals)
