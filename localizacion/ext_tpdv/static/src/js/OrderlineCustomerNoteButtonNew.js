odoo.define('point_of_sale.OrderlineCustomerNoteButtonNew', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class OrderlineCustomerNoteButtonNew extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            const selectedOrder = this.env.pos.get_order();
            if (!selectedOrder) return;

            const { confirmed, payload: inputNote } = await this.showPopup('TextAreaPopup', {
                startingValue: selectedOrder.get_note_receipt(),
                title: this.env._t('Add Customer Note'),
            });

            if (confirmed) {
                selectedOrder.set_note_receipt(inputNote);
            }
        }
    }
    OrderlineCustomerNoteButtonNew.template = 'OrderlineCustomerNoteButtonNew';

    ProductScreen.addControlButton({
        component: OrderlineCustomerNoteButtonNew,
        condition: function() {
            return true;
        },
    });

    Registries.Component.add(OrderlineCustomerNoteButtonNew);

    return OrderlineCustomerNoteButtonNew;
});
