# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models


class TaskCancelWarningWizard(models.TransientModel):
    _name = 'task.cancel.warning.wizard'


class SubTaskCreateWizard(models.TransientModel):
    _name = 'sub.task.create.wizard'
