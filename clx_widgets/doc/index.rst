.. image:: https://www.gnu.org/graphics/lgplv3-147x51.png
   :target: https://www.gnu.org/licenses/lgpl-3.0.en.html
   :alt: License: LGPL-v3

=============
CLX Widgets
=============

This module provides several vidgets for fild representation extend

Usage
=====

There are two ways of using this extension. Field tag in view
definition can be either configured as xref:

1. With attribute

    href_widget="1"

2. As widget (this is only valid way for tree view)

    widget="href_widget"

Example:

 <field name="report_href" widget="clx_href" options="{'display_icon': '1', 'display_url': '0', 'open_new': '1',icon:'fa-bar-chart'}" string="URL" />