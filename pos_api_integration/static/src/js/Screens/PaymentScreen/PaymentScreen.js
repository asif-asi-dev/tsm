odoo.define('pos_api_integration.CustomPaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require("point_of_sale.PaymentScreen");
    const Registries = require("point_of_sale.Registries");

    const PosAPIPaymentScreen = (OriginalPaymentScreen) =>
        class extends OriginalPaymentScreen {
            /**
             * @override
             */

            async validateOrder(isForceValidate) {
                const res = await super.validateOrder(isForceValidate);
                this.push_order_data();
                return res;
            }

            async push_order_data(){
                var orderData = await this.env.services.rpc({
                    model: 'pos.order',
                    method: 'get_order_data',
                    args: [[]]
                });
                var url = this.env.pos.config.pos_order_sync_api;
                if (url && orderData){
                    $.ajax({
                        url: url,
                        type: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify(orderData),
                        success: function(response) {
                            console.log('Success:', response);
                        },
                        error: function(error) {
                            console.error('Error:', error);
                        }
                    });
                }
            }

        };

    Registries.Component.extend(PaymentScreen, PosAPIPaymentScreen);
    return PaymentScreen;
    
});
