from odoo import fields, models, api

import re

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    has_mrp_production = fields.Boolean(
        string="",
        compute="_compute_has_mrp_production",
        store=True
    )

    def _compute_has_mrp_production(self):
        for line in self:
            if line.order_id.state=='sale':
                line.has_mrp_production = bool(self.env['mrp.production'].search([
                    ('origin', '=', line.order_id.name),
                    ('product_id', '=', line.product_id.id)
                ], limit=1))

    def action_view_related_mrp(self):
        production_order = self.env['mrp.production'].search([
            ('origin', '=', self.order_id.name),
            ('product_id', '=', self.product_id.id),
        ], limit=1)

        if production_order:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Manufacturing Order',
                'res_model': 'mrp.production',
                'view_mode': 'form',
                'res_id': production_order.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window_close'
            }

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    shopify_instance_id = fields.Many2one('shopify.credentials', string="Source", compute='_compute_shopify_instance')
    numero_commande = fields.Char(string="Order Number")
    numero_suivi = fields.Char(string="Tracking number")
    sale_order_partner_id = fields.Many2one(related='sale_id.partner_id', string="Client de la commande", store=True)


    def write(self, vals):
        """Override the write method to update the related manufacturing order's picking_scheduled_date when the picking's scheduled date changes."""
        res = super(StockPicking, self).write(vals)

        if 'scheduled_date' in vals:
            for picking in self:
                productions = self.env['mrp.production'].search([('origin', '=', picking.origin)])

                for production in productions:
                    production.write({'picking_scheduled_date': picking.scheduled_date})

        return res

    #deactivate sending confirmation email
    def _send_confirmation_email(self):
        pass

    def send_delivery_email(self):
         email_template = self.env.ref('mrp_production.delivery_confirmation_email_template')
         if email_template:
            # Optional: Set context or parameters for the email
            email_template.send_mail(self.id, force_send=True)

         return True
    

    @api.depends('origin')
    def _compute_shopify_instance(self):
        for picking in self:
            sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
            if sale_order:
                picking.shopify_instance_id = sale_order.shopify_instance_id
            else:
                picking.shopify_instance_id = False


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    image_128 = fields.Image(related='product_id.image_128', string="Image", readonly=True)

        

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    product_qty = fields.Float(string='Quantité', digits=(16, 0))
    note_interne = fields.Text(string="Note")
    logo_inscription = fields.Text(string="Logo/Inscription")
    design_ids = fields.Many2one('kit.design', string='Designs', domain="[('bom_id', '=',bom_id)]")
    remarque_controle_qualite = fields.Text('Remarque Contrôle Qualité')
    product_image=fields.Binary(related='product_id.image_1920' ,string='Image de prouit')
    product_variant_ids=fields.Many2many(related='product_id.product_template_variant_value_ids',string='Caractéristiques')
    product_finalized = fields.Boolean(string='Finition terminée')
    finalization_status = fields.Selection([('finalise', 'Finition terminée'), ('non_finalise', 'Non finalisé')], string='Finition' ,compute='_compute_finalization_status')
    is_conforme = fields.Boolean('Conforme')
    conform_status=fields.Selection([('conforme', 'Conforme'), ('non_conforme', 'Non conforme')], string='Contrôle Qualité', compute='_compute_conforme_status')
    product_tag_ids=fields.Many2many(related='product_id.product_tag_ids' ,string='Étiquettes de modèle de produit')
    color = fields.Char(string='Color', default='No couleur')
    partner_id = fields.Many2one('res.partner', string='Client', help="Client liée a la commande")
    partner_shipping_id = fields.Many2one('res.partner', string="Adresse de livraison", help="Adresse de livraison liée à la commande de vente")
    product_place = fields.Boolean(string='Placé')
    place_status = fields.Selection([('place', 'Placé'), ('non_place', 'Non placé')], string='Placement' ,compute='_compute_placement')
    selected_characteristics = fields.Text(
        string="Caractéristiques",
        compute="_compute_selected_characteristics",
        store=True
    )
   
    color = fields.Char(string="Couleur", compute='_compute_color', store=True)
    years = fields.Char(string="Années", compute='_compute_year', store=True)

    shopify_instance_id = fields.Many2one('shopify.credentials', string="Source", compute='_compute_shopify_instance')
    po_client = fields.Char(string="PO client")
    picking_scheduled_date = fields.Date(string="Must ship by")

    
    def create(self, vals):
        production = super(MrpProduction, self).create(vals)
        
        production.update_picking_scheduled_date()

        return production

    def update_picking_scheduled_date(self):
        for production in self:
            pickings = self.env['stock.picking'].search([('origin', '=', production.name)], limit=1)
            if pickings:
                production.picking_scheduled_date = pickings.scheduled_date
                

    @api.depends('origin')
    def _compute_shopify_instance(self):
        for production in self:
            sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
            if sale_order:
                production.shopify_instance_id = sale_order.shopify_instance_id
            else:
                production.shopify_instance_id = False
    """
    @api.depends('selected_characteristics')
    def _compute_color(self):
        for record in self:
            text = record.selected_characteristics or ''

            # Extract main color, ignoring "No Color"
            main_color_match = re.search(r'MAIN COLOR: ([\w\s]+)', text)
            main_color = main_color_match.group(1) if main_color_match and "No Color" not in main_color_match.group(1) else ''
            
            # Extract carbon code
            carbon_code_match = re.search(r'CARBON CODE: ([\w\s]+)', text)
            carbon_code = carbon_code_match.group(1) if carbon_code_match else ''
            
            # Extract paint code
            paint_code_match = re.search(r'PAINT CODE: ([\w\s]+)', text)
            paint_code = paint_code_match.group(1) if paint_code_match else ''
            
            # Extract insert color
            insert_color_match = re.search(r'INSERT COLOR: ([\w\s]+)', text)
            insert_color = insert_color_match.group(1) if insert_color_match else ''
            
            # Extract interior color (fixing the mistake in the provided example)
            interior_color_match = re.search(r'INTERIOR COLOR: ([\w\s]+)', text)
            interior_color = interior_color_match.group(1) if interior_color_match else ''

            # Concatenate all colors into one field, ignoring empty values
            color_info = []
            if main_color:
                color_info.append(f"Main Color: {main_color}")
            if carbon_code:
                color_info.append(f"Carbon Code: {carbon_code}")
            if paint_code:
                color_info.append(f"Paint Code: {paint_code}")
            if insert_color:
                color_info.append(f"Insert Color: {insert_color}")
            if interior_color:
                color_info.append(f"Interior Color: {interior_color}")

            # Join all color information into a single string
            record.color = ', '.join(color_info) if color_info else 'No Color Information Available'

        """


    @api.depends('selected_characteristics')
    def _compute_year(self):
        for record in self:
            text = record.selected_characteristics or ''
            years_match = re.search(r'Année: ([\w\s]+)', text)
            record.years = years_match.group(1) if years_match and "None" not in years_match.group(1) else ''
        
    @api.depends('selected_characteristics')
    def _compute_color(self):
        for record in self:
            text = record.selected_characteristics or ''
    
            # Extract main color, ignoring "No Color"
            main_color_match = re.search(r'MAIN COLOR: ([\w\s]+)', text)
            main_color = main_color_match.group(1) if main_color_match and "No Color" not in main_color_match.group(1) else ''
            
            # Extract carbon code, ignoring "None"
            carbon_code_match = re.search(r'CARBON CODE: ([\w\s]+)', text)
            carbon_code = carbon_code_match.group(1) if carbon_code_match and "None" not in carbon_code_match.group(1) else ''
            
            # Extract paint code, ignoring "None"
            paint_code_match = re.search(r'PAINT CODE: ([\w\s]+)', text)
            paint_code = paint_code_match.group(1) if paint_code_match and "None" not in paint_code_match.group(1) else ''
            
            # Extract insert color, ignoring "No insert"
            insert_color_match = re.search(r'INSERT COLOR: ([\w\s]+)', text)
            insert_color = insert_color_match.group(1) if insert_color_match and "No insert" not in insert_color_match.group(1) else ''
            
            # Extract interior color, ignoring "No Color"
            interior_color_match = re.search(r'INTERIOR COLOR: ([\w\s]+)', text)
            interior_color = interior_color_match.group(1) if interior_color_match and "No Color" not in interior_color_match.group(1) else ''
    
            # Concatenate all colors into one field, ignoring empty values
            color_info = []
            if main_color:
                color_info.append(f"Main Color: {main_color}")
            if carbon_code:
                color_info.append(f"Carbon Code: {carbon_code}")
            if paint_code:
                color_info.append(f"Paint Code: {paint_code}")
            if insert_color:
                color_info.append(f"Insert Color: {insert_color}")
            if interior_color:
                color_info.append(f"Interior Color: {interior_color}")
    
            # Join all color information into a single string
            record.color = ', '.join(color_info) if color_info else ''

    @api.model
    def create(self, vals):
        # Vérifier si l'ordre de fabrication a une origine (nom de la commande de vente)
        if vals.get('origin'):
            sale_order = self.env['sale.order'].search([('name', '=', vals['origin'])], limit=1)
            if sale_order:
                vals['partner_id'] = sale_order.partner_id.id
                vals['partner_shipping_id'] = sale_order.partner_shipping_id.id
        return super(MrpProduction, self).create(vals)
        
    @api.depends('origin', 'product_id')
    def _compute_selected_characteristics(self):
        
        for production in self:
            production.selected_characteristics = "No characteristics available"

            if production.origin:
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
                        characteristics = sale_order_line.name
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
                
    def _compute_placement(self):
        for production in self:
            if production.product_place:
                production.place_status = 'place'
            else:
                production.place_status = 'non_place'

    

    def _compute_conforme_status(self):
        for production in self:
            if production.is_conforme:
                production.conform_status = 'conforme'
            else:
                production.conform_status = 'non_conforme'
                
        
           
                
