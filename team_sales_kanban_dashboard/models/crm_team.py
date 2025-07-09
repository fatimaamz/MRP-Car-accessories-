from odoo import models, fields, api
from datetime import datetime, timedelta


class CrmTeam(models.Model):
    _inherit = "crm.team"

    dashboard_graph_data_7d = fields.Json(
        string="Graph des 7 derniers jours",
        compute="_compute_dashboard_graph_data_7d",
        store=False
    )

    @api.depends()
    def _compute_dashboard_graph_data_7d(self):
        for team in self:
            now = fields.Datetime.now()
            last_7_days = now - timedelta(days=7)
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', last_7_days),
                ('state', 'in', ['sale', 'done'])
            ])
            grouped_data = {}
            for order in orders:
                day = order.date_order.date().strftime('%Y-%m-%d')
                grouped_data.setdefault(day, 0)
                grouped_data[day] += order.amount_total

            graph_data = {
                'title': 'Commandes - 7 derniers jours',
                'x_axis': 'date_order',
                'y_axis': 'amount_total',
                'graph_type': 'bar',
                'groups': [
                    {'date_order': day, 'amount_total': total}
                    for day, total in sorted(grouped_data.items())
                ]
            }

            team.dashboard_graph_data_7d = graph_data or {}
