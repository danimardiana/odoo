odoo.define('clx_invoice_policy.account.move.tree', function (require) {
"use strict";

var Model = require("web.rpc");
var ListController = require('web.ListController');
var core = require('web.core');

ListController.include({

renderButtons: function($node) {
this._super.apply(this, arguments);
if (this.$buttons) {

let importButton = this.$buttons.find(".oe_auto_generate_invoices");
importButton && importButton.click(this.proxy("AutoGenerateInvoices"));
}
},

AutoGenerateInvoices: function () {
//implement your click logic here
Model.query({
model: "account.move",
method: "generate_invoices",
args: [{}]
}).then(function (data) {
});
}

});
core.action_registry.add('clx_invoice_policy.account.move.tree', ListController);
return ListController;
});


