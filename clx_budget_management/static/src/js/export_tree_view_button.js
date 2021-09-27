odoo.define('clx_budget_management.tree_view_button', function (require){
    "use strict";
    
    var core = require('web.core');
    var ListView = require('web.ListView');
    var ListController = require("web.ListController"); 
    
    var IncludeListView = {
            renderButtons: function($node) {
                this._super.apply(this, arguments);
                if (this.modelName === "sale.budget.exports") {
                    var summary_apply_leave_btn = this.$buttons.find('button.generate_exports');              
                    summary_apply_leave_btn.on('click', this.proxy('tree_view_action'))
                }
            },
    
            tree_view_action: function () {      
                var self = this;
                var action = {
                        type: "ir.actions.act_window",
                        name: "budget_exports",
                        res_model: "sale.budget.export.wizard",
                        views: [[false,'form']],
                        target: 'new',
                        view_type : 'form',
                        view_mode : 'form',
                        flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
            }
            return this.do_action(action);
                // { 'type': 'ir.actions.client','tag': 'reload', } 
        }
    }
    ListController.include(IncludeListView);
    });