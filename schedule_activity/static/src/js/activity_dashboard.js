odoo.define('schedule_activity.dashboard', function(require) {
    "use strict";
    var core = require('web.core');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var Widget = require('web.Widget');
    var AbstractAction = require('web.AbstractAction');
    var QWeb = core.qweb;
    var _t = core._t;
    var _lt = core._lt;

    var ActivityDashboardView = AbstractAction.extend({
        template: 'acitvity_dashboard.dashboard',
        events: {
            'click .upcoming_activities': 'action_upcoming_activities',
            'click .todays_activities': 'action_todays_activities',
            'click .late_activities': 'action_late_activities',
            'click  .mark-done': 'action_done',
            'click  .activity': 'action_open_activity',
        },
        init: function(parent, context) {
            this._super(parent, context);
            var activity_data = [];
            var res = ''
            var self = this;
            self.render()

        },

        willStart: function() {
            var self = this;
            return $.when(ajax.loadLibs(this), this._super()).then(function() {
                return self.fetch_data();
            });
        },


        fetch_data: function() {
            var activity_data = [];
            var res = ''
            var self = this;
            var def1 = this._rpc({
                model: 'activity.details',
                method: 'get_activity_info'
            }).then(function(result) {
                if (result) {
                    self.activity_data = result[0]
                    res = result
                    if (res.length != 0) {

                        var todays_activity = res[0]['todays_acitvities_count']
                        var upcoming_activity = res[0]['upcoming_acitvities_count']
                        var overdue_activity = res[0]['overdue_acitvities_count']
                        $('.todays').append('<span style="display:block;font-size:50px;color:#FFF;font-weight:500; margin:-13px 10px 75px 50px;">' + todays_activity + '</span>')
                        $('.upcoming').append('<span style="display:block;font-size:50px;color:#FFF;font-weight:500; margin:-13px 10px 75px 50px;">' + upcoming_activity + '</span>')
                        $('.overdue').append('<span style="display:block;font-size:50px;color:#FFF;font-weight:500; margin:-13px 10px 75px 50px;">' + overdue_activity + '</span>')
                        for (var i = 0; i < res.length; i++) {
                            if (res[i].todays_activities_id) {
                                $('.today .data_body').append('<tr><td class="activity_name activity"><span style="cursor: pointer;" >' + res[i].todays_activities_name + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].type + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].assigned_to + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].supervisor + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].date_deadline + '</span></td>' +
                                    '<input type="hidden" name="activity_id" value="' + res[i].todays_activities_id + '" id="h_v"  activity_id="' + res[i].todays_activities_id + '"/></td>' +
                                    '<td><button style="cursor: pointer;" class="btn-success mark-done">Mark As Done</button></td></tr>')
                            } else if (res[i].upcoming_activities_id) {

                                $('.activity_table .data_body').append('<tr><td class="activity_name activity"><span style="cursor: pointer;">' + res[i].upcoming_activities_name + '</span>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].type + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].assigned_to + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].supervisor + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].date_deadline + '</span></td>' +
                                    '<input type="hidden" name="activity_id" value="' + res[i].upcoming_activities_id + '" id="h_v"  activity_id="' + res[i].upcoming_activities_id + '"/></td>' +
                                    '<td><button style="cursor: pointer;" class="btn-success mark-done">Mark As Done</button></td></tr>')
                            } else if (res[i].overdue_activities_id) {
                                $('.overdue_activities .data_body').append('<tr><td class="activity_name activity"><span style="cursor: pointer;">' + res[i].overdue_activities_name + '</span>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].type + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].assigned_to + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].supervisor + '</span></td>' +
                                    '<td><span style="cursor: pointer;" >' + res[i].date_deadline + '</span></td>' +
                                    '<input type="hidden" name="activity_id" value="' + res[i].overdue_activities_id + '" id="h_v"  activity_id="' + res[i].overdue_activities_id + '"/></td>' +
                                    '<td><button style="cursor: pointer;" class="btn-success mark-done">Mark As Done</button></td></tr>')
                            }


                        }
                    }
                }

            });
        },

        render: function() {
            var self = this;
            var activity_dashboard = QWeb.render('acitvity_dashboard.dashboard', {
                widget: self,
            });
            $(activity_dashboard).prependTo(self.$el);
            return activity_dashboard
        },
        reload: function() {

            location.reload();

        },
        action_upcoming_activities: function(event) {
            var self = this;
            var today = new moment().utc().format();
            event.stopPropagation();
            event.preventDefault();
            this.do_action({
                name: _t("Upcoming Activities"),
                type: 'ir.actions.act_window',
                res_model: 'mail.activity',
                view_mode: 'tree,form',
                view_type: 'form',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
                domain: [
                    ['user_id', '=', session.uid],
                    ['date_deadline', '>', today]
                ],
            }, {

            })
        },


        action_late_activities: function(event) {
            var self = this;
            var today = new moment().utc().format();
            event.stopPropagation();
            event.preventDefault();
            this.do_action({
                name: _t("Late Activities"),
                type: 'ir.actions.act_window',
                res_model: 'mail.activity',
                view_mode: 'tree,form',
                view_type: 'form',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                target: 'current',
                domain: [
                    ['user_id', '=', session.uid],
                    ['date_deadline', '<', today]
                ],

            }, {

            })
        },
        action_todays_activities: function(event) {
            var self = this;
            var today = new moment().utc().format();
            event.stopPropagation();
            event.preventDefault();
            this.do_action({
                name: _t("Todays Activities"),
                type: 'ir.actions.act_window',
                res_model: 'mail.activity',
                view_mode: 'tree,form',
                view_type: 'form',
                views: [
                    [false, 'list'],
                    [false, 'form']
                ],
                domain: [
                    ['user_id', '=', session.uid],
                    ['date_deadline', '=', today]
                ],
                target: 'current'
            }, {

            })
        },

        action_open_activity: function(event) {
            var self = this;
            var today = new moment().utc().format();
            event.stopPropagation();
            event.preventDefault();
            var $el = $(event.target).parents('tr').find("#h_v").attr("value")
            var activity_id = parseInt($el)
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mail.activity',
                res_id: activity_id,
                views: [
                    [false, 'form']
                ],
                target: 'current'
            }, {

            })
        },


        action_done: function(e) {
            var self = this;
            var today = new moment().utc().format();
            event.stopPropagation();
            event.preventDefault();
            var $el = $(e.target).parents('tr').find("#h_v").attr("value")
            var activity_id = parseInt($el)
            this._rpc({
                model: 'mail.activity',
                method: 'action_done',
                args: [activity_id],
            }).then(function() {
                self.reload();
            });
        },

    });
    core.action_registry.add('schedule_activity.dashboard', ActivityDashboardView);
    return {
        ActivityDashboardView: ActivityDashboardView
    }

});