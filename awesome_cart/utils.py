# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string

def update_context(context):

	path = frappe.local.request.path[1:]
	print("Path: %s" % frappe.local.request.path)

	context.current_date = ''

	#if path == 'cart':
	#	from .templates.pages import cart
	#	cart.get_context(context)
	#
	#	log("Context for: \n%s" % json.dumps(context, indent=2, default=json_default))
