odoo.define('clx_ratio_invoice.clx.ratio.invoice.template', function (require) {
    'use strict';

    var Model = require('web.rpc');
    var ajax = require('web.ajax');
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            let self = this;

            // Get the Coop Tree element and use it as
            // the starting point for moving up/down
            // and making changes to relative elements
            let coopTree = $('.coop_ratio_tree');

            if (self.$buttons && coopTree.length > 0) {
                let splitButton = coopTree.closest('.modal-content').find('.oe_split_ratio_button');
                let createButton = coopTree.closest('.modal-content').find('.o_list_button_add');
                let discardButton = coopTree.closest('.modal-content').find('.o_list_button_discard');
                let saveButton = coopTree.closest('.modal-content').find('.o_list_button_save');
                let exportButton = coopTree.closest('.modal-content').find('.o_list_export_xlsx');

                splitButton && splitButton.click(self.proxy('SplitRatioEvenly'));
                exportButton.hide();

                coopTree.closest('.modal-content').find('.o_list_button_add').text('ADD');

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
                coopTree.closest('.modal-content').find('.o_cp_left, .o_cp_right, .o_searchview').hide();
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
            });

            Model.query({
                model: 'co.op.sale.order.partner',
                method: 'split_ratio_evenly',
                args: [{}],
                kwargs: { split_ratio: ratio, sale_order_line_id: sale_order_line_id }
            }).then(function (data) {});
        }
    });
});
