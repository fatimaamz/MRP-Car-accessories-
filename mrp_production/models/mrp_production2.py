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
    color = fields.Char(string='Couleur', default='No couleur')
    


    selected_characteristics = fields.Text(
        string="Caractéristiques",
        compute="_compute_selected_characteristics",
        store=True
    )

    @api.depends('origin', 'product_id')
    def _compute_selected_characteristics(self):
        for production in self:
            production.selected_characteristics = "No characteristics available"

            if production.sale_order_origin:
                # Search for the sale order with the matching origin
                sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
                if sale_order:
                    # Find the sale order line with the same product_id
                    sale_order_line = self.env['sale.order.line'].search([
                        ('order_id', '=', sale_order.id),
                        ('product_id', '=', production.product_id.id)
                    ], limit=1)
                    if sale_order_line:
                        # Extract characteristics from the sale order line's name
                        characteristics = sale_order_line.name.split('\n')[-1]
                        production.selected_characteristics = characteristics
                else:
                    break
            else:
                break

    
    
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            for variant in self.product_id.product_template_attribute_value_ids:
                if variant.attribute_id.name.lower() == 'interior colors':
                    color_attribute = variant.name
                    self.color = color_attribute
    
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
                
        
           
                
