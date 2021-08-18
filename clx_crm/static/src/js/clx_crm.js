odoo.define('clx_crm.lead.contact.validation.template', function (require) {
    'use strict';

    var Model = require('web.rpc');
    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            // Get the existing contact tree element and use it as
            // the starting point for moving up/down
            // and making changes to relative elements
            let existingContactTree = $('.existing_contact_tree');

            // onClick handelers to allow only one checkbox per grouping,
            // disable sorting and disablethe select all checkbox
            existingContactTree.find('th.o_list_record_selector').find('div.custom-control').hide();
            existingContactTree.find('th.o_column_sortable').removeClass('o_column_sortable');
            existingContactTree.find('.custom-control-input').click(res => {
                let checkbox = res.target;
                if (checkbox.checked) {
                    $(checkbox)
                        .closest('tbody')
                        .find('tr')
                        .each((idx, tr) => {
                            let cb = $(tr).find('input:checkbox');
                            if (checkbox.id != cb[0].id) {
                                cb[0].checked = false;
                            }
                        });
                }
            });

            if (this.$buttons && this.modelName === 'lead.contact.validation') {
                let selectedContactsBtn = existingContactTree
                    .closest('.modal-content')
                    .find('.save_varification_button');
                let exportButton = existingContactTree.closest('.modal-content').find('.o_list_export_xlsx');
                let discardButton = existingContactTree.closest('.modal-content').find('.o_list_button_discard');

                // add handlers
                selectedContactsBtn && selectedContactsBtn.click(this.proxy('saveSelectedContactOptions'));

                // Remove unused search bar elements from header
                exportButton.hide();
                existingContactTree.closest('.modal-content').find('.o_cp_left').hide();
                existingContactTree.closest('.modal-content').find('.o_cp_right').hide();
                existingContactTree.closest('.modal-content').find('.o_searchview').hide();
            }
        },

        saveSelectedContactOptions: function () {
            var selected_records = this.getSelectedRecords();
            var data = [];

            for (var rec of selected_records) {
                data.push(rec.data);
            }

            Model.query({
                model: 'lead.contact.validation',
                method: 'save_contact_choices',
                args: [{}],
                kwargs: { contacts: data }
            }).then(function (data) {});
        }
    });
});
