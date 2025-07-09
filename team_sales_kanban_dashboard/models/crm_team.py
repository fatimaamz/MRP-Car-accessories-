from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo import models, fields, api
from datetime import datetime, timedelta

class CrmTeam(models.Model):
    _inherit = "crm.team"

    dashboard_graph_data_7d = fields.Binary(
        string="Dashboard Graph (7d)",
        compute="_compute_dashboard_graph_data_7d"
    )

    @api.depends()
    def _compute_dashboard_graph_data_7d(self):
        for team in self:
            last_7_days = fields.Datetime.to_string(datetime.now() - timedelta(days=7))
            orders = self.env['sale.order'].read_group(
                domain=[
                    ('team_id', '=', team.id),
                    ('date_order', '>=', last_7_days),
                    ('state', 'in', ['sale', 'done'])  # pour les commandes confirmées
                ],
                fields=['amount_total', 'date_order:day'],
                groupby=['date_order:day'],
                lazy=False,
            )
            graph_data = {
                'title': 'Commandes - 7 derniers jours',
                'x_axis': 'date_order',
                'y_axis': 'amount_total',
                'groups': orders,
                'graph_type': 'bar'
            }
            team.dashboard_graph_data_7d = graph_data
