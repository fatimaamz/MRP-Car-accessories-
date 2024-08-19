from odoo import models, fields, api
from datetime import date

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    discounted_amount_total = fields.Monetary(string='Discounted Amount Total', compute='_compute_discounted_amount_total', store=True)

    @api.depends('order_line.price_total', 'partner_id')
    def _compute_discounted_amount_total(self):
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
                        order.discounted_amount_total = discounted_total

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        order._compute_discounted_amount_total()
        return order

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self._compute_discounted_amount_total()
        return res
