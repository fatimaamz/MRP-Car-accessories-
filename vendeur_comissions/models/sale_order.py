from odoo import models, fields, api
from datetime import timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    installation_effectuee = fields.Boolean(string="Installation Effectuée", default=False)
    installateurs_ids = fields.Many2many('res.users', string="Installateurs")
    vente_oem = fields.Boolean(string="Vente OEM", default=False)
    territory_id = fields.Many2one(
        'sales.territory', string="Territory",
        related="partner_id.territory_id", store=True
    )

    @api.model
    def create(self, vals):
        invoice = super(AccountMove, self).create(vals)
        invoice._calculate_commissions()
        return invoice

    def _calculate_commissions(self):
        for invoice in self:
            # Définir les taux de commission
            commission_rate_installed = 0.10
            commission_rate_oem = 0.05
            commission_pool_rate = 0.10
            bonus_rate_high = 0.15

            # Récupérer le territoire et l'objectif
            territory = invoice.territory_id
            if not territory:
                continue

            # Calcul des ventes hebdomadaires pour le territoire
            start_of_week = fields.Date.today() - timedelta(days=fields.Date.today().weekday())
            end_of_week = start_of_week + timedelta(days=6)
            weekly_invoices = self.env['account.move'].search([
                ('territory_id', '=', territory.id),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', start_of_week),
                ('invoice_date', '<=', end_of_week),
            ])

            total_installed_sales = sum(inv.amount_total for inv in weekly_invoices if inv.installation_effectuee)
            total_oem_sales_real = sum(inv.amount_total for inv in weekly_invoices if inv.vente_oem)

            # Limiter les ventes OEM à 30% des ventes installées
            total_oem_sales_permitted = min(total_oem_sales_real, total_installed_sales * 0.30)
            total_weekly_sales = total_installed_sales + total_oem_sales_permitted

            # Calcul du *Commission Pool*
            commission_pool = 0
            if total_weekly_sales > territory.weekly_target * 1.5:
                commission_pool = (total_weekly_sales - territory.weekly_target * 1.5) * bonus_rate_high
            elif total_weekly_sales > territory.weekly_target:
                commission_pool = (total_weekly_sales - territory.weekly_target) * commission_pool_rate

            # Calcul des commissions individuelles
            for installer in invoice.installateurs_ids:
                commission_amount_installed = invoice.amount_total * commission_rate_installed / len(invoice.installateurs_ids)
                self.env['sales.commission'].create({
                    'user_id': installer.id,
                    'invoice_id': invoice.id,
                    'commission_amount': commission_amount_installed,
                })

            if invoice.vente_oem:
                commission_amount_oem = invoice.amount_total * commission_rate_oem
                self.env['sales.commission'].create({
                    'user_id': invoice.user_id.id,
                    'invoice_id': invoice.id,
                    'commission_amount': commission_amount_oem,
                })

            # Répartition du *Commission Pool* selon les jours travaillés
            #total_days_worked = sum(rep.days_worked for rep in territory.representatives_ids)
            #for representative in territory.representatives_ids:
                #share = representative.days_worked / total_days_worked if total_days_worked else 0
                #self.env['sales.commission'].create({
                  #  'user_id': representative.id,
                  #  'territory_id': territory.id,
                   # 'commission_amount': share * commission_pool,
               # })
