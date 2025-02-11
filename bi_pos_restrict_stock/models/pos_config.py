# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
import json


class PosConfig(models.Model):
	_inherit = "pos.config"

	display_stock = fields.Boolean(string='Display Stock in POS')
	restrict_product = fields.Boolean(string='Restrict Product Out of Stock in POS')
	stock_type = fields.Selection(
		[('onhand', 'Qty on Hand'), ('virtual', 'Virtual Qty'), ('both', 'Both')], string='Stock Type',default='onhand')


class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'


	pos_display_stock = fields.Boolean(related='pos_config_id.display_stock',readonly=False)
	pos_restrict_product = fields.Boolean(related='pos_config_id.restrict_product',readonly=False)
	pos_stock_type = fields.Selection(related='pos_config_id.stock_type',readonly=False)



class Product(models.Model):
	_inherit = 'product.product'

	quant_ids = fields.One2many("stock.quant", "product_id", string="Quants",
								domain=[('location_id.usage', '=', 'internal')])

	quant_text = fields.Text('Quant Qty', compute='_compute_avail_locations', store=True)

	@api.depends('stock_quant_ids', 'stock_quant_ids.product_id', 'stock_quant_ids.location_id',
				 'stock_quant_ids.quantity')
	def _compute_avail_locations(self):
		for rec in self:
			final_data = {}
			rec.sudo().quant_text = json.dumps(final_data)
			if rec.type == 'product':
				quants = self.env['stock.quant'].sudo().search(
					[('product_id', 'in', rec.ids), ('location_id.usage', '=', 'internal')])
				outgoing = self.env['stock.move'].sudo().search(
					[('product_id', '=', rec.id), ('state', 'not in', ['done']),
					 ('location_id.usage', '=', 'internal'),
					 ('picking_id.picking_type_code', 'in', ['outgoing'])])
				incoming = self.env['stock.move'].sudo().search(
					[('product_id', '=', rec.id), ('state', 'not in', ['done']),
					 ('location_dest_id.usage', '=', 'internal'),
					 ('picking_id.picking_type_code', 'in', ['incoming'])])
				for quant in quants:
					loc = quant.location_id.id
					if loc in final_data:
						last_qty = final_data[loc][0]
						final_data[loc][0] = last_qty + quant.quantity
					else:
						final_data[loc] = [quant.quantity, 0, 0]

				for out in outgoing:
					loc = out.location_id.id
					if loc in final_data:
						last_qty = final_data[loc][1]
						final_data[loc][1] = last_qty + out.product_qty
					else:
						final_data[loc] = [0, out.product_qty, 0]

				for inc in incoming:
					loc = inc.location_dest_id.id
					if loc in final_data:
						last_qty = final_data[loc][2]
						final_data[loc][2] = last_qty + inc.product_qty
					else:
						final_data[loc] = [0, 0, inc.product_qty]
				rec.sudo().quant_text = json.dumps(final_data)
		return True

class PosSession(models.Model):
	_inherit = 'pos.session'


	def _loader_params_product_product(self):
		result = super()._loader_params_product_product()
		result['search_params']['fields'].extend(['type','virtual_available','qty_available','incoming_qty','outgoing_qty','quant_ids','quant_text'])
		return result

	def _pos_ui_models_to_load(self):
		result = super()._pos_ui_models_to_load()
		result.extend(['stock.location'])
		return result

	def _loader_params_stock_picking_type(self):
		result = super()._loader_params_stock_picking_type()
		result['search_params']['fields'].append('warehouse_id')
		return result

	def _loader_params_stock_location(self):
		return {
			'search_params': {
				'domain': [],
				'fields': [],
			}
		}

	def _get_pos_ui_stock_location(self, params):
		return self.env['stock.location'].search_read(**params['search_params'])

	def _pos_data_process(self, loaded_data):
		super()._pos_data_process(loaded_data)
		
		loc_by_id={}
		for rec in loaded_data['stock.location']:
			loc_by_id[rec['id']]=rec
		loaded_data['pos_custom_location'] = loaded_data['stock.location']
		

class stock_move(models.Model):
	_inherit = 'stock.move'

	@api.model
	def sync_product(self, prd_id):
		notifications = []
		ssn_obj = self.env['pos.session'].sudo()
		prod_fields = ssn_obj._loader_params_product_product()['search_params']['fields']
		prod_obj = self.env['product.product'].sudo()

		product = prod_obj.with_context(display_default_code=False).search_read([('id', '=', prd_id)],prod_fields)
		product_id = prod_obj.search([('id', '=', prd_id)]) 

		res = product_id._compute_quantities_dict(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'), self._context.get('from_date'), self._context.get('to_date'))
		product[0]['qty_available'] = res[product_id.id]['qty_available']
		if product :
			categories = ssn_obj._get_pos_ui_product_category(ssn_obj._loader_params_product_category())
			product_category_by_id = {category['id']: category for category in categories}
			product[0]['categ'] = product_category_by_id[product[0]['categ_id'][0]]

			vals = {
				'id': [product[0].get('id')], 
				'product': product,
				'access':'pos.sync.product',
			}
			notifications.append([self.env.user.partner_id,'product.product/sync_data',vals])
		if len(notifications) > 0:
			self.env['bus.bus']._sendmany(notifications)
		return True


	@api.model_create_multi
	def create(self, vals_list):
		res = super(stock_move, self).create(vals_list)
		notifications = []
		for rec in res:
			rec.product_id._compute_avail_locations()
			rec.sync_product(rec.product_id.id)
		return res

	def write(self, vals):
		res = super(stock_move, self).write(vals)
		notifications = []
		for rec in self:
			rec.product_id._compute_avail_locations()
			rec.sync_product(rec.product_id.id)
		return res


