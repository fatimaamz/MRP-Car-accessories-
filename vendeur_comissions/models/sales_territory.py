from odoo import models, fields



class SalesTerritory(models.Model):
    _name = 'sales.territory'
    _description = 'Sales Territory'

    #name = fields.Char(string="Territory Name", required=True)
    #weekly_target = fields.Float(string="Weekly Target", required=True)
    #representative_ids = fields.Many2many(
        #'res.users', string="Assigned Representatives"
    #)
    name = fields.Char(string="Nom du Territoire", required=True)
    objectif_hebdomadaire = fields.Float(string="Objectif Hebdomadaire ($)", required=True)


class SalesCommission(models.Model):
    _name = 'sales.commission'
    _description = 'Sales Commission'

    #user_id = fields.Many2one('res.users', string="Representative", required=True)
    #invoice_id = fields.Many2one('account.move', string="Invoice", required=True)
    #commission_amount = fields.Float(string="Commission Amount", required=True)
    #commission_date = fields.Date(string="Commission Date", default=fields.Date.today)


    @api.model
    def calculer_commissions(self):
        # Obtenir les territoires existants
        territoires = self.env['sales.territory'].search([])
        rapports_commissions = []

        for territoire in territoires:
            # Récupérer les factures pour le territoire et la semaine en cours
            factures = self.env['account.move'].search([
                ('territoire_id', '=', territoire.id),
                ('state', '=', 'posted'),  # Factures validées
                ('invoice_date', '>=', fields.Date.today() - timedelta(days=7))
            ])

            # Séparer les ventes installées et OEM
            ventes_installees = sum(factures.filtered(lambda f: f.installation_effectuee).mapped('amount_total'))
            ventes_oem_reelles = sum(factures.filtered(lambda f: f.vente_oem).mapped('amount_total'))
            ventes_oem_permises = min(ventes_oem_reelles, ventes_installees * 0.3)
            ventes_totales = ventes_installees + ventes_oem_permises

            # Calculer le pool de commissions
            taux_commission = 0.1 if ventes_totales < (territoire.objectif_hebdomadaire * 1.5) else 0.15
            pool_commission = max(ventes_totales - territoire.objectif_hebdomadaire, 0) * taux_commission

            # Répartition des commissions du pool entre les représentants
            representants = factures.mapped('installateurs_ids')
            jours_travailles = {rep.id: len(representants.filtered(lambda r: r.id == rep.id)) for rep in representants}
            total_jours = sum(jours_travailles.values())

            for rep in representants:
                commission_pool = (jours_travailles[rep.id] / total_jours) * pool_commission if total_jours > 0 else 0
                commission_directe = sum(factures.filtered(lambda f: rep in f.installateurs_ids).mapped('amount_total')) * 0.1
                commission_oem = sum(factures.filtered(lambda f: f.vente_oem and rep in f.installateurs_ids).mapped('amount_total')) * 0.05

                rapports_commissions.append({
                    'representant': rep.name,
                    'territoire': territoire.nom,
                    'pool_commission': commission_pool,
                    'commission_directe': commission_directe,
                    'commission_oem': commission_oem,
                    'total': commission_pool + commission_directe + commission_oem,
                })

        return rapports_commissions

class AccountMove(models.Model):
    _inherit = 'account.move'

    territoire_id = fields.Many2one('territoire', string="Territoire", required=True)
    installation_effectuee = fields.Boolean(string="Installation Effectuée", default=False)
    installateurs_ids = fields.Many2many('res.users', string="Installateurs")
    vente_oem = fields.Boolean(string="Vente OEM", default=False)
