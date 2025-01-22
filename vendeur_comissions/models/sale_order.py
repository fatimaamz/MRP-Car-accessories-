from odoo import models, fields, api,_
from datetime import timedelta

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    weekly_target = fields.Float(
        string="Objectif Hebdomadaire ($)",
        help="Définir l'objectif hebdomadaire pour cette équipe."
    )

class SalesRepAttendance(models.Model):
    _name = 'sales.rep.attendance'
    _description = 'Attendance des Vendeurs'

    sales_rep_id = fields.Many2one(
        'res.users',
        string="Vendeur",
        required=True,
        domain="[('id', 'in', allowed_sales_reps)]"
    )
    team_id = fields.Many2one('crm.team', string="Équipe", required=True)
    week_start_date = fields.Date(string="Début de la Semaine", required=True)
    days_worked = fields.Integer(string="Jours Travaillés", required=True)

    allowed_sales_reps = fields.Many2many(
        'res.users',
        compute='_compute_allowed_sales_reps',
        string="Vendeurs Disponibles"
    )

    @api.depends('team_id')
    def _compute_allowed_sales_reps(self):
        """Calculer les vendeurs autorisés en fonction de l'équipe sélectionnée."""
        for record in self:
            if record.team_id:
                record.allowed_sales_reps = record.team_id.member_ids
            else:
                record.allowed_sales_reps = self.env['res.users'].browse()

    _sql_constraints = [
        ('unique_attendance', 'unique(sales_rep_id, team_id, week_start_date)',
         'Un enregistrement existe déjà pour ce vendeur, cette équipe, et cette semaine.')
    ]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    installation = fields.Boolean(
        string="Installation",
        help="Indique si une installation est incluse pour cette commande.",
        default=lambda self: self._get_default_installation()
    )

    def _get_default_installation(self):
        # Check if the customer type is 'Concessionnaires régulier'
        if self.partner_id and self.type_client == 'Concessionnaires Régulier':
            return True
        return False
        
    type_client = fields.Selection(
        related='partner_id.type_client',
        string="Type de client",
        store=True
    )

    team_weekly_target = fields.Float(
        string="Objectif Hebdomadaire ($)",
        compute='_compute_team_weekly_target',
        store=True
    )
    commission_pool = fields.Float(
        string="Commission Pool",
        compute='_compute_commission_pool',
        store=True
    )
    individual_commissions = fields.Float(
        string="Commissions Individuelles",
        compute='_compute_individual_commissions',
        store=True
    )

    
            
    @api.depends('user_id')
    def _compute_team_weekly_target(self):
        """Récupérer l'objectif hebdomadaire de l'équipe du vendeur associé."""
        for order in self:
            # Rechercher l'équipe de vente associée à l'utilisateur
            team = self.env['crm.team'].search([('member_ids', 'in', [order.user_id.id])], limit=1)
            if team:
                order.team_weekly_target = team.weekly_target
            else:
                order.team_weekly_target = 0 

    @api.depends('amount_total', 'team_weekly_target')
    def _compute_commission_pool(self):
        """Calcul du commission pool en fonction des objectifs atteints."""
        for order in self:
            if order.amount_total > order.team_weekly_target:
                bonus_rate = 0.15 if order.amount_total >= 1.5 * order.team_weekly_target else 0.10
                order.commission_pool = (order.amount_total - order.team_weekly_target) * bonus_rate
            else:
                order.commission_pool = 0

    additional_commission = fields.Float(
            string="Commission Additionnelle",
            compute='_compute_individual_commissions',
            store=True
        )

    @api.depends('user_id', 'commission_pool', 'team_id', 'amount_total', 'installation')
    def _compute_individual_commissions(self):
        """Calcul des commissions individuelles basées sur les jours travaillés et installation."""
        for order in self:
            attendances = self.env['sales.rep.attendance'].search([
                ('team_id', '=', order.team_id.id),
                ('week_start_date', '<=', fields.Date.today()),
                ('week_start_date', '>=', fields.Date.today() - timedelta(days=7))
            ])
            total_days_worked = sum(attendances.mapped('days_worked'))

            if total_days_worked > 0:
                per_day_rate = order.commission_pool / total_days_worked
                base_commissions = sum([
                    att.days_worked * per_day_rate
                    for att in attendances if att.sales_rep_id == order.user_id
                ])
            else:
                base_commissions = 0

            # Ajouter 10 % de commission si l'installation est activée
            if order.installation:
                order.additional_commission = order.amount_total * 0.10
            else:
                order.additional_commission = 0

            order.individual_commissions = base_commissions + order.additional_commission

