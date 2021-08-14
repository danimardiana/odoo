"use strict";
/**
 * Copyright Conversion Logix
 * License LGPLv3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.en.html).
 *
 */

odoo.define('clx_href', function (require) {
    const FieldChar = require("web.basic_fields").FieldChar;
    
    // const setClipboard = require("web_clipboard.set_clipboard");
    const field_registry = require('web.field_registry');
    const core = require('web.core');
    const _t = core._t;

    FieldChar.include({
        events: Object.assign({}, FieldChar.prototype.events, {
            'click .clx-href': '_onHrefButtonClick',
        }),
        init() {
            this._super.apply(this, arguments);
            this.nodeOptions.isHref = 'clx-href' in this.attrs;
        },
        // start: function () {
        //     let counter = '<i class="fa fa-link"/>';
            //this.$el.replaceWith(counter)
        // },
        _formatElement: function(){
            const arguments = this.nodeOptions
            let resultHtml = ''
            let resultTarget = ''
            if (arguments.hasOwnProperty('open_new') && parseInt(arguments.open_new)) {
                resultTarget = 'target="_blank"'
            }
            if (arguments.hasOwnProperty('display_icon') && parseInt(arguments.display_icon)) {
                iconType = arguments.hasOwnProperty('icon')?arguments.icon:'fa-link'
                resultHtml += '<a class="btn btn-default clx-href" href="'+this.value+'" '+resultTarget+'><i class="fa '+iconType+'"/></a>'
            }            
            if (arguments.hasOwnProperty('display_url') && parseInt(arguments.display_url)) {
                resultHtml += '<a class="clx-href" href="'+this.value+'" '+resultTarget+'>'+this.value+'</a>'
            }
            return resultHtml
        },
        _render: function () {
            this._super.apply(this, arguments);
            if (this.nodeOptions.isHref) {
                if (this.value) {
                    this.$el.html(this._formatElement());
                    this.$el.attr('title', this.value);
                    this.$el.attr('aria-label', this.value);
                }
                // this.$el.replaceWith(this._formatElement())
            }
        },
        _onHrefButtonClick(event) {
            const arguments = this.nodeOptions;
            event.preventDefault();
            event.stopPropagation();
            let target = ''
            if (arguments.hasOwnProperty('open_new') && parseInt(arguments.open_new)) {
                target = '_blank'
            }
            window.open(this.value,target );
        },
    });
    const clxHrefChar = FieldChar.extend({
        init() {
            this._super.apply(this, arguments);
            this.nodeOptions.isHref = true;
        },
    });
    field_registry.add("clx_href", clxHrefChar);
    return clxHrefChar;
});
