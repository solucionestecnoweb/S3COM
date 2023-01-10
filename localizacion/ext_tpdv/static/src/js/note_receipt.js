odoo.define('ext_tpdv.note_receipt', function (require) {
"use strict";

var models = require('point_of_sale.models');

var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
    initialize: function(attr, options) {
        _super_order.initialize.call(this,attr,options);
        this.note_receipt = this.note_receipt || "";
    },
    set_note_receipt: function(note_receipt){
        this.note_receipt = note_receipt;
        this.trigger('change',this);
    },
    get_note_receipt: function(note){
        return this.note_receipt;
    },
    export_as_JSON: function(){
        var json = _super_order.export_as_JSON.call(this);
        json.note_receipt = this.note_receipt;
        return json;
    },
    init_from_JSON: function(json){
        _super_order.init_from_JSON.apply(this,arguments);
        this.note_receipt = json.note_receipt;
    },
    export_for_printing: function() {
        var json = _super_order.export_for_printing.apply(this,arguments);
        debugger;
        json.note_receipt = this.note_receipt;
        return json;
    },

});


});