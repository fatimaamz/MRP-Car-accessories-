# -*- coding: utf-8 -*-

from odoo import models,fields,api


class YearModel(models.Model):
    _name = 'year.model'
    _description = 'Year Model'

    name = fields.Integer(string='Year', required=True, unique=True)


class ProductMark(models.Model):
    _name = 'product.modele'
    _description = 'Product model'

    name = fields.Char(string='model', required=True)
class ProductSousModele(models.Model):
    _name = 'product.sousmodele'
    _description = 'Product Sous modele'

    name = fields.Char(string='Sous modèle', required=True)

class ProductStyle(models.Model):
    _name = 'product.style'
    _description = 'Product Style'

    name = fields.Char(string='Name', required=True)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    year_ids = fields.Many2many('year.model', string='Année')
    product_type = fields.Selection([
        ('exterior', 'Exterior'),
        ('moulding', 'Moulding'),
        ('interior', 'Interior'),
        ('grill', 'Grill')
    ], string='Product Type')

    priceA = fields.Float(string='Price A')
    priceB = fields.Float(string='Price B')
    priceC = fields.Float(string='Price C')
    priceD = fields.Float(string='Price D')

    modele_id = fields.Many2one('product.mark', string='Mark')
    sous_model_id = fields.Many2one('product.sousmodele', string='Sous modèle')
    style_id = fields.Many2one('product.style', string='Style')
