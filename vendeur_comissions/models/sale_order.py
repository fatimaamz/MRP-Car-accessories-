from odoo import models, fields,api,_

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    territory_id = fields.Many2one(
        'sales.territory', string="Territory",
        related="partner_id.territory_id", store=True
    )

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({
            'territory_id': self.territory_id.id,
        })
        return invoice_vals


class AccountMove(models.Model):
    _inherit = 'account.move'

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
            # Calculer la commission basée sur la vente
            commission_rate = 0.10  # Par défaut pour les ventes installées

            # Calculer le montant total des ventes du territoire pour vérifier l'objectif atteint
            territory = invoice.territory_id
            if territory:
                sales_total = self.env['account.move'].search([
                    ('territory_id', '=', territory.id),
                    ('state', '=', 'posted')
                ]).filtered(lambda m: m.invoice_date.week == fields.Date.today().week).amount_total

                # Calcul du bonus basé sur l'objectif du territoire
                commission_pool = 0
                if sales_total > territory.weekly_target * 1.5:
                    commission_pool = (sales_total - territory.weekly_target * 1.5) * 0.15
                elif sales_total > territory.weekly_target:
                    commission_pool = (sales_total - territory.weekly_target) * 0.10

                # Appliquer la commission pool à la vente installée
                total_commission = invoice.amount_total * commission_rate + commission_pool

                # Diviser la commission entre les représentants en fonction de l'installation
                if invoice.user_id:
                    self.env['sales.commission'].create({
                        'user_id': invoice.user_id.id,
                        'invoice_id': invoice.id,
                        'commission_amount': total_commission,
                    })