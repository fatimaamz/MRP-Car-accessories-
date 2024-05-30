from odoo import fields, models, api

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    design_ids = fields.Many2one('kit.design', string='Designs', domain="[('bom_id', '=',bom_id)]")
    remarque_controle_qualite = fields.Text('Remarque Contrôle Qualité')
    product_image=fields.Binary(related='product_id.image_1920' ,string='Image de prouit')
    product_variant_ids=fields.Many2many(related='product_id.product_template_variant_value_ids',string='Caractéristiques')
    product_finalized = fields.Boolean(string='Finition terminée')
    finalization_status = fields.Selection([('finalise', 'Finition terminée'), ('non_finalise', 'Non finalisé')], string='Statut Finition' ,compute='_compute_finalization_status')
    is_conforme = fields.Boolean('Conforme')
    conform_status=fields.Selection([('conforme', 'Conforme'), ('non_conforme', 'Non conforme')], string='Statut Contrôle Qualité', compute='_compute_conforme_status')
    product_tag_ids=fields.Many2many(related='product_id.product_tag_ids' ,string='Étiquettes de modèle de produit')
    
    def _compute_finalization_status(self):
        for production in self:
            if production.product_finalized:
                production.finalization_status = 'finalise'
            else:
                production.finalization_status = 'non_finalise'

    

    def _compute_conforme_status(self):
        for production in self:
            if production.is_conforme:
                production.conform_status = 'conforme'
            else:
                production.conform_status = 'non_conforme'
                
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for line in order.order_line:
                if line.product_id.type == 'product' and line.product_id.bom_ids:
                    manufacturing_order = self.env['mrp.production'].create({
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom_id': line.product_uom.id,
                        'origin': order.name,
                        'bom_id': line.product_id.bom_ids[0].id,
                    })
                    manufacturing_order.action_confirm()
        return res
  
           
                
