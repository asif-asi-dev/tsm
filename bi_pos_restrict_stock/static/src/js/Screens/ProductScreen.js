odoo.define('bi_pos_restrict_stock.ProductScreen', function(require) {
	"use strict";

	const Registries = require('point_of_sale.Registries');
	const ProductScreen = require('point_of_sale.ProductScreen');
    const { onMounted } = owl;

	const BiProductScreen = (ProductScreen) =>
		class extends ProductScreen {
			setup() {
                super.setup();
            }

			// async _clickProduct(event) {
			// 	let self = this;
            //     const product = event.detail;
            //     var order = self.env.pos.get_order();
            //     let call_super = true;
			// 	if(self.env.pos.config.display_stock && product.type == 'product'){
            //         if (self.env.pos.config.restrict_product == true){
            //             if(self.env.pos.config.stock_type == "onhand"){
            //                 if (product.qty_available <= 0){
            //                     call_super = false;
            //                     self.showPopup('BiWarningPopup', {
            //                         product: product,
            //                         name: product.display_name,
            //                     });
            //                 }
			// 		    }else if(self.env.pos.config.stock_type == "virtual"){
            //                 if (product.virtual_available <= 0){
            //                     call_super = false;
            //                     self.showPopup('BiWarningPopup', {
            //                         product: product,
            //                         name: product.display_name,
            //                     });
            //                 }
			// 		    }
            //             else if(self.env.pos.config.stock_type == "both"){
            //                 if (product.qty_available <= 0){
            //                     call_super = false;
            //                     self.showPopup('BiWarningPopup', {
            //                         product: product,
            //                         name: product.display_name,
            //                     });
            //                 }
            //                 else if (product.virtual_available <= 0){
            //                     call_super = false;
            //                     self.showPopup('BiWarningPopup', {
            //                         product: product,
            //                         name: product.display_name,
            //                     });
            //                 }
            //             }
			// 		}
            //     }
            //     if(call_super){
            //         super._clickProduct(event);
            //     }
            //     this.showScreen('PaymentScreen');
            //     this.showScreen('ProductScreen');
			// }

			async _setValue(val) {
                var self = this
                if (this.currentOrder.get_selected_orderline()) {
                    var line = this.currentOrder.get_selected_orderline()
                    if(self.env.pos.config.display_stock && line.product.type == 'product' && self.env.pos.config.restrict_product == true){
                        if (this.env.pos.numpadMode === 'quantity') {
                            if(val != 'remove' && val != ''){
                                if(self.env.pos.config.stock_type == "onhand"){
                                    if (line.product.qty_available < val){
                                        self.showPopup('BiWarningPopup', {
                                            product: line.product,
                                            name: line.product.display_name,
                                            quantity: val
                                        });
                                    }else{
                                        line.set_quantity(val);
                                    }
                                }else if(self.env.pos.config.stock_type == "virtual"){
                                    if (line.product.virtual_available < val){
                                        self.showPopup('BiWarningPopup', {
                                            product: line.product,
                                            name: line.product.display_name,
                                            quantity: val,
                                        });
                                    }
                                    else{
                                        line.set_quantity(val);
                                    }
                                }
                                else if(self.env.pos.config.stock_type == "both"){
                                    if (line.product.virtual_available < val){
                                        self.showPopup('BiWarningPopup', {
                                            product: line.product,
                                            name: line.product.display_name,
                                            quantity: val,
                                        });
                                    }
                                    else if (line.product.qty_available < val){
                                        self.showPopup('BiWarningPopup', {
                                            product: line.product,
                                            name: line.product.display_name,
                                            quantity: val,
                                        });
                                    }else{
                                        line.set_quantity(val);
                                    }
                                }
                            }else{
                                super._setValue(...arguments);
                            }
                        }else{
                            super._setValue(...arguments);
                        }
                    }else{
                        super._setValue(...arguments);
                    }
                }
            }
		};

	Registries.Component.extend(ProductScreen, BiProductScreen);

	return ProductScreen;

});
