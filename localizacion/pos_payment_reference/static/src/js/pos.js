odoo.define('pos_payment_reference.pos_payment_reference', function (require) {
"use strict";

    const models = require('point_of_sale.models');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');

    const PaymentScreen2 = (PaymentScreen) => {
        class PaymentScreen2 extends PaymentScreen {
            constructor() {
                super(...arguments);
                useListener('onKeydown-ref', this.onKeydown_ref);
            }

            onKeydown_ref(event) {
                const { cid } = event.detail;
                const line = this.paymentLines.find((line) => line.cid === cid);
                line.payment_refer = $(".paymentline.selected").find(".payment_refer").val();
            }

        }
        return PaymentScreen2;
    };
    Registries.Component.extend(PaymentScreen, PaymentScreen2);


    var PaymentlineSuper = models.Paymentline;
    models.Paymentline = models.Paymentline.extend({
        initialize: function(attributes, options){
            var self = this;
            PaymentlineSuper.prototype.initialize.apply(this, arguments);
            this.payment_refer = "";
        },
        export_as_JSON: function(){
            var data = PaymentlineSuper.prototype.export_as_JSON.apply(this, arguments);
            data.payment_refer = this.payment_refer;
            return data;
        }
    });
});

