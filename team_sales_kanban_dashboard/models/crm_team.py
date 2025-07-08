from odoo import models, fields, api
from datetime import timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    quote_count = fields.Integer(string="Nombre de devis", compute="_compute_sales_stats", store=False)
    order_to_invoice_count = fields.Integer(string="Commandes à facturer", compute="_compute_sales_stats", store=False)
    total_sales = fields.Float(string="Total des ventes", compute="_compute_sales_stats", store=False)
    sales_by_day = fields.Char(string="Ventes par jour", compute="_compute_sales_stats", store=False)

    @api.depends()
    def _compute_sales_stats(self):
        today = fields.Date.today()
        past_7 = today - timedelta(days=6)

        for team in self:
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', past_7)
            ])
            quotes = orders.filtered(lambda s: s.state in ['draft', 'sent'])
            to_invoice = orders.filtered(lambda s: s.invoice_status == 'to invoice')
            confirmed = orders.filtered(lambda s: s.state in ['sale', 'done'])
            total = sum(confirmed.mapped('amount_total'))

            # Ventes journalières
            daily = []
            for i in range(7):
                date = today - timedelta(days=i)
                amount = sum(confirmed.filtered(lambda o: o.date_order.date() == date).mapped('amount_total'))
                daily.append(str(int(amount)))
            daily.reverse()

            team.quote_count = len(quotes)
            team.order_to_invoice_count = len(to_invoice)
            team.total_sales = total
            team.sales_by_day = ','.join(daily)
