odoo.define('bi_pos_restrict_stock.models', function(require) {
    "use strict";

    const { PosGlobalState, Order, Orderline, Payment } = require('point_of_sale.models');
    var { Gui } = require('point_of_sale.Gui');

    
    const Registries = require('point_of_sale.Registries');
    const PosHomePosGlobalState = (PosGlobalState) => class PosHomePosGlobalState extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.locations = loadedData['stock.location'];
            this.warningpopup = false;
            
        }
    }
    Registries.Model.extend(PosGlobalState, PosHomePosGlobalState);


    const PosOrder = (Order) => class PosOrder extends Order {
        get_display_product_qty(prd){
            var self = this;
            var products = {};
            var order = this.pos.get_order();
            var display_qty = 0;
            if(order){
                var orderlines = order.get_orderlines();
                if(orderlines.length > 0){
                    orderlines.forEach(function (line) {
                        if(line.product['id'] == prd.id){
                            display_qty += line.get_quantity()
                        }
                    });
                }
            }
            return display_qty
        }

        add_product(product, options){
            let self = this;
            let call_super = true;
            if(self.pos.config.display_stock && product.type == 'product' && this.pos.warningpopup == false){
                if (self.pos.config.restrict_product == true){
                    if(self.pos.config.stock_type == "onhand"){
                        if (product.qty_available <= 0){
                            call_super = false;
                            Gui.showPopup('BiWarningPopup', {
                                product: product,
                                name: product.display_name,
                                option: options,
                            });
                        }
                    }else if(self.pos.config.stock_type == "virtual"){
                        if (product.virtual_available <= 0){
                            call_super = false;
                            Gui.showPopup('BiWarningPopup', {
                                product: product,
                                name: product.display_name,
                                option: options,
                            });
                        }
                    }
                    else if(self.pos.config.stock_type == "both"){
                        if (product.qty_available <= 0){
                            call_super = false;
                            Gui.showPopup('BiWarningPopup', {
                                product: product,
                                name: product.display_name,
                                option: options,
                            });
                        }
                        else if (product.virtual_available <= 0){
                            call_super = false;
                            Gui.showPopup('BiWarningPopup', {
                                product: product,
                                name: product.display_name,
                                option: options,
                            });
                        }
                    }
                }
            }
            if(call_super){
                this.pos.warningpopup = false;
                super.add_product(...arguments);
            }
        }
    }
    Registries.Model.extend(Order, PosOrder);
});
