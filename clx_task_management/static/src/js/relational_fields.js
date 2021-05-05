odoo.define('clx_task_management.custom_stage_confirm', function (require) {
    'use strict';

    //require the module to modify:
    const relational_fields = require('web.relational_fields');

    //override the method:
    relational_fields.FieldStatus.include({
        /**
         * Called when on status stage is clicked -> sets the field value.
         * @private
         * @param {MouseEvent} e
         */
        _onClickStage: function (e) {
            let self = this;
            e.stopPropagation();
            e.preventDefault();

            // Only open proof return form if clicked status is proof return(18)
            if ($(e.currentTarget).data('value') === 18) {
                self._rpc({
                    model: 'ir.model.data',
                    method: 'xmlid_to_res_id',
                    kwargs: { xmlid: 'clx_task_management.view_task_proof_return_form' }
                })
                    .then(function (view_id) {
                        let context = self.record.context;
                        context.current_task = self.res_id;

                        self.do_action({
                            type: 'ir.actions.act_window',
                            name: _('Proof Return'),
                            res_model: 'task.proof.return',
                            target: 'new',
                            view_mode: 'form',
                            views: [[view_id, 'form']],
                            context: context
                        });
                    })
                    .then(function (res) {});
            } else {
                self._setValue($(e.currentTarget).data('value'));
            }
        }
    });
});
