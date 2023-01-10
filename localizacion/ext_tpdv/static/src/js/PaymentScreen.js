odoo.define('ext_tpdv.PaymentScreen', function(require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    var core = require('web.core');
    var _t = core._t;

    const PosNotePaymentScreenFields = PaymentScreen => class extends PaymentScreen {
        async validateOrder(isForceValidate) {
            var order = this.env.pos.get_order();
            console.log("inh por sustitucion")
            if(this.env.pos.config.customer_required && !order.get_client()) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Cliente requerido'),
                    body: this.env._t('Seleccione el cliente antes de validar el pedido!'),
                });
                return;
            }
            if(this.env.pos.config.vat_required && !order.get_client().vat) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Cedula del cliente requerido'),
                    body: this.env._t('Seleccione un cliente con cedula antes de validar el pedido!'),
                });
                return;
            }
            if(this.env.pos.config.street_required && !order.get_client().street) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Direccion del cliente requerido'),
                    body: this.env._t('Seleccione un cliente con direccion antes de validar el pedido!'),
                });
                return;
            }
            if(this.env.pos.config.phone_required && !order.get_client().phone) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Telefono del cliente requerido'),
                    body: this.env._t('Seleccione un cliente con telefono antes de validar el pedido!'),
                });
                return;
            }
            else {
                super.validateOrder(...arguments);
            }
        }
    };

    Registries.Component.extend(PaymentScreen, PosNotePaymentScreenFields);

    return PaymentScreen;
});
