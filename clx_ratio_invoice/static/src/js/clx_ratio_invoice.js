odoo.define('clx_ratio_invoice.clx.ratio.invoice.template', function (require) {
    'use strict';

    var Model = require('web.rpc');
    var ajax = require('web.ajax');
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            var self = this;
            if (self.$buttons) {
                let splitButton = this.$buttons.find('.oe_split_ratio_button');
                let createButton = this.$buttons.find('.o_list_button_add');
                let discardButton = this.$buttons.find('.o_list_button_discard');
                let saveButton = this.$buttons.find('.o_list_button_save');
                let exportButton = this.$buttons.find('.o_list_export_xlsx');
                //let toolBarButtons = $('.o_cp_buttons');

                splitButton && splitButton.click(self.proxy('SplitRatioEvenly'));
                exportButton.hide();

                createButton.text('ADD');

                // add handlers for toogleing(hide/show) the split button
                createButton.click(() => {
                    $('.oe_split_ratio_button').hide();
                });
                discardButton.click(() => {
                    $('.oe_split_ratio_button').show();
                });
                saveButton.click(() => {
                    $('.oe_split_ratio_button').show();
                });
                $('tr.o_data_row').click(() => {
                    $('.oe_split_ratio_button').hide();
                });

                // Remove unused search bar elements from header
                $('.o_cp_left').hide();
                $('.o_cp_right').hide();
                $('.o_searchview').hide();
            }
        },

        SplitRatioEvenly: function () {
            let self = this;
            let count = self.$('tbody.ui-sortable tr.o_data_row').length;
            let tableBody = self.$('tbody.ui-sortable');
            let ratio = count > 0 ? 100 / count : 0;
            let sale_order_line_id = self.initialState.context.default_sale_order_line_id;

            tableBody.find('tr.o_data_row').each((idx, tr) => {
                let split_ratio = $(tr).find('td.o_list_number');
                split_ratio.text(ratio.toFixed(2));

                // console.log(self.initialState.context.default_sale_order_line_id);
                // console.log(`Actual ratio: ${ratio}`);
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
