odoo.define('new_tab_widget.tree_view', function (require) {
"use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        events: _.extend({}, ListRenderer.prototype.events, {
            'click .o_external_button': '_onExternalButtonClicked',
        }),
        _onExternalButtonClicked: function(ev){
            ev.preventDefault();
            ev.stopPropagation();
            var url = window.location.href;
            var base_url = url.split("#")[0];
            if (base_url !== null && ev.currentTarget.getAttribute("href") !== null) {
                window.open(base_url + ev.currentTarget.getAttribute("href"));
            }
        },
        _renderExternalLinkHeader: function(){
            var $content = $('<div/>', {
            });

            return $('<th>')
            .addClass('o_list_record_selector')
            .append($content);
        },
        _renderExternalLink: function (url) {
            var $content = $('<div/>', {
            });
            var $anchor = $('<a/>', {
                href: url,
                class: 'fa fa-external-link o_external_button',
            });
            $content.append($anchor);

            return $('<td>')
            .addClass('o_list_record_selector')
            .append($content);
        },
        _renderRow: function (record) {
            var $tr = this._super.apply(this, arguments);
            var base_url =$.bbq.getState(true)
            if (this.hasSelectors || [this.state.model,'board.board'].indexOf(base_url.model) > -1
                || !base_url.model) {
                var queryString = window.location.hash.substring(1);
                var urlParams = new URLSearchParams(queryString);
                var menuId = urlParams.get('menu_id') || '';
                var action = urlParams.get('action') || '';
                var model = this.state.model;
                var active_id = urlParams.get('active_id') || null;
                var url = '#id=' + record.res_id + '&model=' + model + '&menu_id=' + menuId;
                if (base_url.model == this.state.model){
                        url = url + '&action=' + action;
                    }
                if (active_id !== null){
                        url = url + '&active_id=' + active_id;
                    }
                url = url +'&view_type=form';
                $tr.prepend(this._renderExternalLink(url));
            }            

            return $tr;
        },

        _renderHeader: function () {
            var base_url =$.bbq.getState(true)
            var $tr = $('<tr>')
                .append(_.map(this.columns, this._renderHeaderCell.bind(this)));
            if (this.hasSelectors) {
                $tr.prepend(this._renderSelector('th'));
                $tr.prepend(this._renderExternalLinkHeader());
            }
            else if([this.state.model,'board.board'].indexOf(base_url.model)> -1
                || !base_url.model){
                $tr.prepend(this._renderExternalLinkHeader());
            }
            return $('<thead>').append($tr);
        },

        _renderFooter: function () {
            var aggregates = {};
            _.each(this.columns, function (column) {
                if ('aggregate' in column) {
                    aggregates[column.attrs.name] = column.aggregate;
                }
            });
            var $cells = this._renderAggregateCells(aggregates);
            if (this.hasSelectors) {
                $cells.unshift($('<td>'));
                $cells.unshift($('<td>'));
            }
            return $('<tfoot>').append($('<tr>').append($cells));
        },

        _getNumberOfCols: function () {
            var n = this.columns.length;
            return this.hasSelectors ? n + 2 : n;
        },
    });

});