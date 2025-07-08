from odoo import models, fields, api
from datetime import timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    order_count = fields.Integer(string="Commandes confirmées", compute="_compute_sales_stats", store=False)
    total_sales = fields.Float(string="Total ventes", compute="_compute_sales_stats", store=False)
    sales_by_day = fields.Char(string="Ventes quotidiennes", compute="_compute_sales_stats", store=False)

    @api.depends()
    def _compute_sales_stats(self):
        today = fields.Date.today()
        past_7 = today - timedelta(days=6)

        for team in self:
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', past_7),
                ('state', 'in', ['sale', 'done']),
            ])
            team.order_count = len(orders)
            team.total_sales = sum(orders.mapped('amount_total'))

            # Bar chart data: ventes par jour
            daily = []
            for i in range(7):
                date = today - timedelta(days=i)
                daily_total = sum(orders.filtered(lambda o: o.date_order.date() == date).mapped('amount_total'))
                daily.append(str(int(daily_total)))
            team.sales_by_day = ','.join(reversed(daily))
