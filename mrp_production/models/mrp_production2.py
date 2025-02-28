from odoo import fields, models, api

import re

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    has_mrp_production = fields.Boolean(
        string="",
        compute="_compute_has_mrp_production",
        default=False
    )

    def _compute_has_mrp_production(self):
        for line in self:
            if line.order_id.state=='sale':
                line.has_mrp_production = bool(self.env['mrp.production'].search([
                    ('origin', '=', line.order_id.name),
                    ('product_id', '=', line.product_id.id)
                ], limit=1))
            else:
                line.has_mrp_production = False

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
    sale_order_partner_id = fields.Many2one(related='sale_id.partner_id', string="Client de la commande")


  

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

    
    new_design = fields.Selection(
        [
            ('requis', 'Requis'),
            ('recu', 'Reçu'),
        ],
        string="Nouveau Design",
        default='requis',  # Optional: Set a default value
        help="Indicate the design status as either Requis or Reçu."
    )
    interior_color = fields.Char(string="Interior Color", compute="_compute_interior_color", store=True)
    insert_color = fields.Char(string="Insert Color", compute="_compute_insert_color", store=True)
    main_color = fields.Char(string="Main Color", compute="_compute_main_color", store=True)
    carbon_code = fields.Char(string="Carbon Code", compute="_compute_carbon_code", store=True)
    paint_code = fields.Char(string="Paint Code", compute="_compute_paint_code", store=True)
    year = fields.Char(string="Year", compute="_compute_year", store=True)

    @api.depends('selected_characteristics')
    def _compute_interior_color(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'^INTERIOR COLOR:\s*(.*)', text, re.MULTILINE)
            record.interior_color = match.group(1).strip() if match else ''

    @api.depends('selected_characteristics')
    def _compute_insert_color(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'^INSERT COLOR:\s*(.*)', text, re.MULTILINE)
            value = match.group(1).strip() if match else ''
            record.insert_color = '' if value.lower() == "not applicable" else value

    @api.depends('selected_characteristics')
    def _compute_paint_code(self):
        for record in self:
            text = record.selected_characteristics or ''
            # Recherche strictement sur la ligne "PAINT CODE:" pour éviter les erreurs
            match = re.search(r'^PAINT CODE:\s*(.*)', text, re.MULTILINE)
            value = match.group(1).strip() if match else ''
            record.paint_code = value

    @api.depends('selected_characteristics')
    def _compute_main_color(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'^Couleurs:\s*(.*)', text, re.MULTILINE)
            record.main_color = match.group(1).strip() if match else ''
    
    
    """
    @api.depends('selected_characteristics')
    def _compute_interior_color(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'INTERIOR COLOR:\s*(.+?)(?:\n|$)', text)
            record.interior_color = match.group(1).strip() if match else ''

   
            
    
    @api.depends('selected_characteristics')
    def _compute_insert_color(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'INSERT COLOR:\s*(.+?)(?:\n|$)', text)
            record.insert_color = match.group(1).strip() if match else ''

    @api.depends('selected_characteristics')
    def _compute_main_color(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'Couleurs:\s*(.+?)(?:\n|$)', text)
            record.main_color = match.group(1).strip() if match else ''

    @api.depends('selected_characteristics')
    def _compute_carbon_code(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'CARBON CODE:\s*(.+?)(?:\n|$)', text)
            record.carbon_code = match.group(1).strip() if match else ''
    
    @api.depends('selected_characteristics')
    def _compute_paint_code(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'PAINT CODE:\s*(.+?)(?:\n|$)', text)
            record.paint_code = match.group(1).strip() if match else ''
    """
  
    @api.depends('selected_characteristics')
    def _compute_year(self):
        for record in self:
            text = record.selected_characteristics or ''
            match = re.search(r'Année:\s*(.+?)(?:\n|$)', text)
            record.year = match.group(1).strip() if match else ''

    product_template_id = fields.Many2one(
        related='product_id.product_tmpl_id',
        string="Product Template",
        store=True,
        readonly=True
    )
    
    product_image_id = fields.Many2one(
        'product.image',
        string="Production Image",
        domain="[('product_id', '=', product_id)]",
        ondelete='set null',
        compute='_compute_product_image_id',  # Computed field
        inverse='_inverse_product_image_id',
        store=True,
        help="Select an image for this production."
    )
    
    @api.depends('product_id')
    def _compute_product_image_id(self):
        """Compute the first product image based on product_id."""
        for record in self:
            if record.product_id:
                first_image = self.env['product.image'].search(
                    [('product_id', '=', record.product_id.id)]
                )
                record.product_image_id = first_image[0].id if first_image else False
                
               
    def _inverse_product_image_id(self):
        """Inverse method to set the product image manually."""
        for sale in self:
            if sale.product_id:
                continue

    
        
    
  
    selected_image = fields.Image(
        string="Image",
        compute="_onchange_product_image_id",
        
        help="Image selected for this production."
    )

    @api.onchange('product_image_id')
    def _onchange_product_image_id(self):
        """Trigger UI refresh when product_image_id is changed."""
        for record in self:
            # Log the selected image to ensure the change is captured
            if record.product_image_id:
                record.selected_image = record.product_image_id.image

    product_qty = fields.Float(string='Quantité', digits=(16, 0))
    note_interne = fields.Text(string="Note")
    logo_inscription = fields.Text(string="Logo/Inscription")
    design_ids = fields.Many2one('kit.design', string='Designs', domain="[('bom_id', '=',bom_id)]")
    remarque_controle_qualite = fields.Text('Remarque Contrôle Qualité')
    product_image=fields.Binary(related='product_id.image_1920' ,string='Image de prouit')
    product_variant_ids=fields.Many2many(related='product_id.product_template_variant_value_ids',string='Caractéristiques')
    product_finalized = fields.Boolean(string='Finition terminée')
    finalization_status = fields.Selection([('finalise', 'Finition terminée'), ('non_finalise', 'Non finalisé')], string='Finition' ,compute='_compute_finalization_status')
    is_conforme = fields.Boolean('Conformité')
    conform_status=fields.Selection([('conforme', 'Conforme'), ('non_conforme', 'Non conforme')], string='Quality Control', compute='_compute_conforme_status')
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
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Sale Order',
        compute='_compute_sale_order',
        store=True,)
  
    po_client = fields.Char(string="PO client",related='sale_order_id.client_order_ref')
  
    ship_to_id = fields.Many2one('res.partner', string="Ship To", compute="_compute_ship_to_id")
    picking_id = fields.Many2one('stock.picking', string="Stock Picking", compute="_compute_picking_id")
    picking_scheduled_date = fields.Datetime(related='picking_id.scheduled_date', string="Must Ship By")
    is_coped= fields.Boolean(string="Coupé", compute="_compute_is_coped")

    product_ref = fields.Char(string="Reference", compute="_compute_product_ref", store=True)
    product_model = fields.Char(string="Model", compute="_compute_product_ref", store=True)
    product_brand = fields.Char(string="Brand", compute="_compute_product_ref", store=True)
    product_style = fields.Char(string="Style", compute="_compute_product_ref", store=True)

    @api.depends('origin')
    def _compute_sale_order(self):
        for record in self:
            if record.origin:  
                sale_order = self.env['sale.order'].search([('name', '=', record.origin)], limit=1)
                record.sale_order_id = sale_order.id if sale_order else False
            else:
                record.sale_order_id = False


    def action_view_delivery_order(self):
        delivery_order = self.env['stock.picking'].search([('origin', '=', self.origin)], limit=1)
        if delivery_order:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bon de Livraison',
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'res_id': delivery_order.id,
                'target': 'current',
            }
        else:
            return {'type': 'ir.actions.act_window_close'}


            

    @api.depends('state')  
    def _compute_is_coped(self):
        for production in self:
            if production.state in ['confirmed','done']:
                production.is_coped=True
            else:
               production.is_coped=False 
            
  

    @api.depends('origin')
    def _compute_picking_id(self):
        for production in self:
            if not production.origin:
                production.picking_id = False
                continue  # On évite d'exécuter une recherche inutile

            picking = self.env['stock.picking'].search([
                ('origin', '=', production.origin),
                ('state', 'not in', ['cancel'])
            ], limit=1)

            production.picking_id = picking.id if picking else False



 
    

    @api.depends('origin')
    def _compute_ship_to_id(self):
        for production in self:
            sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
            if sale_order:
                production.ship_to_id = sale_order.partner_shipping_id
            else:
                production.ship_to_id = False

    

    @api.depends('origin')
    def _compute_shopify_instance(self):
        for production in self:
            sale_order = self.env['sale.order'].search([('name', '=', production.origin)], limit=1)
            if sale_order:
                production.shopify_instance_id = sale_order.shopify_instance_id
            else:
                production.shopify_instance_id = False

    @api.depends('product_id.name')
    def _compute_product_ref(self):
        for record in self:
            if record.product_id and record.product_id.name:
                # Extract the reference part (everything before the space)
                ref_match = re.match(r'^#?([^\s]+)\s*\((.*?)\)$', record.product_id.name)
                if ref_match:
                    record.product_ref = ref_match.group(1)
                    # Split the components inside parentheses
                    components = [x.strip() for x in ref_match.group(2).split(',')]
                    record.product_model = components[0] if len(components) > 0 else ''
                    record.product_brand = components[1] if len(components) > 1 else ''
                    record.product_style = components[2] if len(components) > 2 else ''
                else:
                    record.product_ref = ''
                    record.product_model = ''
                    record.product_brand = ''
                    record.product_style = ''
            else:
                record.product_ref = ''
                record.product_model = ''
                record.product_brand = ''
                record.product_style = ''

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
                
        
           
                
