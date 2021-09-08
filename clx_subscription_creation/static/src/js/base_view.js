odoo.define('clx_subscription_creation.BasicView', function (require) {
    "use strict";
    var session = require('web.session');
    var BasicView = require('web.BasicView');
    BasicView.include({
            init: function(viewInfo, params) {
                var self = this;
                this._super.apply(this, arguments);
                var model = self.controllerParams.modelName;
                if( model == 'sale.subscription' || model == 'sale.subscription.line' ) {
                    session.user_has_group('clx_subscription_creation.subscription_deletion_group').then(function(has_group) {
                        if(!has_group) {
                            self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
                        }
                    });
                }
            },
    });
    });