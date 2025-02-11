from odoo import fields, models, api
import requests

class PosOrder(models.Model):
    _inherit = "pos.order"

    def get_order_data(self):
        order = self.search([], order="id desc", limit=1)
        order_lines = []
        for line in order.lines:
            lot_data = []
            for lot in line.pack_lot_ids:
                lot_data.append({
                    'lot_id': lot.id,
                    'lot_name': lot.lot_name,
                    'product': lot.product_id.id,
                    'quantity': 0.0,
                })
            order_lines.append({
                'product': line.product_id.id,
                'quantity': line.qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'subtotal': line.price_subtotal,
                'tax': line.price_subtotal_incl - line.price_subtotal,
                'subtotal_incl': line.price_subtotal_incl,
                'lots': lot_data
            })
        payment_lines = []
        for line in order.payment_ids:
            payment_lines.append({
                'payment_date': line.payment_date.strftime("%d-%m-%Y %H:%M:%S"),
                'payment_method': line.payment_method_id.id,
                'amount': line.amount 
            })
        order_data = {
            'reference': order.name,
            'pos_reference': order.pos_reference,
            'total': order.amount_total,
            'date': order.date_order.strftime("%d-%m-%Y %H:%M:%S"),
            'session': order.session_id.id,
            'user': order.user_id.id,
            'customer': order.partner_id.id,
            'status': order.state,
            'orderlines': order_lines,
            'payment_data': payment_lines
        }
        return order_data