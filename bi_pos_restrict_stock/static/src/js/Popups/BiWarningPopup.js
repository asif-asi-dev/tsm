odoo.define('bi_pos_restrict_stock.BiWarningPopup', function(require) {
	'use strict';

	const PosComponent = require('point_of_sale.PosComponent');
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	const Registries = require('point_of_sale.Registries');
    let pos_model = require('point_of_sale.models');

	class BiWarningPopup extends AbstractAwaitablePopup {
	    setup() {
			super.setup();
        }

        async order(){
            var self = this;
            var order = self.env.pos.get_order();
            if(self.props.quantity){
	            var orderline = order.get_selected_orderline();
	            orderline.set_quantity(self.props.quantity);
	        }else{
	        	self.env.pos.warningpopup = true;
	            order.add_product(self.props.product, self.props.option);
	        }
	        self.env.posbus.trigger('close-popup', {
	                popupId: self.props.id,
	                response: { confirmed: true, payload: await self.getPayload() },
	         });
            self.showScreen('ProductScreen');
        }
	}

	BiWarningPopup.template = 'BiWarningPopup';
	Registries.Component.add(BiWarningPopup);
	return BiWarningPopup;
});
