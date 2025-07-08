from odoo import models, fields, api
from datetime import timedelta

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    sale_order_ids = fields.One2many('sale.order', 'team_id', string="Orders")
    quote_count = fields.Integer(string="Nombre de devis", compute="_compute_team_stats")
    order_count = fields.Integer(string="Commandes confirmées", compute="_compute_team_stats")
    total_sales = fields.Float(string="Total ventes", compute="_compute_team_stats")
    weekly_sales = fields.Char(string="Ventes par jour", compute="_compute_team_stats")

    @api.depends('sale_order_ids')
    def _compute_team_stats(self):
        for team in self:
            today = fields.Date.today()
            last_week = today - timedelta(days=7)
            orders = self.env['sale.order'].search([
                ('team_id', '=', team.id),
                ('date_order', '>=', last_week)
            ])

            team.quote_count = len(orders.filtered(lambda o: o.state in ['draft', 'sent']))
            team.order_count = len(orders.filtered(lambda o: o.state in ['sale', 'done']))
            team.total_sales = sum(orders.filtered(lambda o: o.state in ['sale', 'done']).mapped('amount_total'))

            bars = []
            for i in range(7):
                day = today - timedelta(days=i)
                daily_total = sum(orders.filtered(lambda o: o.date_order.date() == day).mapped('amount_total'))
                bars.append(str(int(daily_total)))
            team.weekly_sales = ','.join(reversed(bars))
