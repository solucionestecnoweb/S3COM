odoo.define('pw_customer_required.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;

    const PosNotePaymentScreen = PaymentScreen => class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            var order = this.env.pos.get_order();
            debugger;
            if(this.env.pos.config.customer_required && !order.get_client()) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Cliente requerido'),
                    body: this.env._t('Seleccione el cliente antes de validar el pedido!'),
                });
                return;
            }
            
            else {
                super.validateOrder(...arguments);
            }
        }
    };

    Registries.Component.extend(PaymentScreen, PosNotePaymentScreen);

    return PaymentScreen;
});
