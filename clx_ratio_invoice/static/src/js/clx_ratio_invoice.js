odoo.define('clx_ratio_invoice.clx.ratio.invoice.template', function (require) {
    'use strict';

    var Model = require('web.rpc');
    var ajax = require('web.ajax');
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            var self = this;
            if (this.$buttons) {
                let splitButton = this.$buttons.find('.oe_split_ratio_button');
                splitButton && splitButton.click(this.proxy('SplitRatioEvenly'));
            }
        },

        SplitRatioEvenly: function () {
            let self = this;
            let count = self.$('tbody.ui-sortable tr.o_data_row').length;
            let tableBody = self.$('tbody.ui-sortable');
            let ratio = count > 0 ? 100 / count : 0;
            let sale_order_line_id = self.initialState.context.default_sale_order_line_id;

            tableBody.find('tr.o_data_row').each((idx, tr) => {
                let partner = $(tr).find('td.o_list_many2one');
                let split_ratio = $(tr).find('td.o_list_number');
                split_ratio.text(ratio.toFixed(2));

                console.log(self.initialState.context.default_sale_order_line_id);
                console.log(`Actual ratio: ${ratio}`);
            });

            Model.query({
                model: 'co.op.sale.order.partner',
                method: 'split_ratio_evenly',
                args: [{}],
                kwargs: { split_ratio: ratio, sale_order_line_id: sale_order_line_id }
            }).then(function (data) {
                //console.log('SET RATIO(S)');
            });
        }
    });
});

// odoo.define('clx_ratio_invoice.coop.ratio.tree', function (require) {
//     'use strict';

//     var Model = require('web.rpc');
//     var ListController = require('web.ListController');
//     var core = require('web.core');

//     ListView.include({
//         renderButtons: function ($node) {
//             this._super.apply(this, arguments);
//             if (this.$buttons) {
//                 console.log('ADD BUTTON!!!!!!!');
//                 let importButton = this.$buttons.find('.oe_split_ratio_button');
//                 importButton && importButton.click(this.proxy('SplitRatioEvenly'));
//             }
//         },
//         // ListView.include({
//         //     renderButtons: function (data) {
//         //         if (this.$buttons) {
//         //             console.log('ADD BUTTON!!!!!!!');
//         //             this.$buttons.find('.oe_split_ratio_button').click(this.proxy('SplitRatioEvenly'));
//         //         }
//         //     },

//         SplitRatioEvenly: function () {
//             //implement your click logic here
//             // Model.query({
//             //     model: 'account.move',
//             //     method: 'generate_invoices',
//             //     args: [{}]
//             // }).then(function (data) {});
//         }
//     });
//     core.action_registry.add('clx_ratio_invoice.coop.ratio.tree', ListView);
//     return ListView;
// });
