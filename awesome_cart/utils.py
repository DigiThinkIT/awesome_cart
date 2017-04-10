# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback

from frappe import _
from frappe.utils import random_string

from .dbug import pretty_json

def update_context(context):

	path = frappe.local.request.path[1:]
	print("Path: %s" % frappe.local.request.path)
	context.current_date = ''


def on_session_creation(login_manager):
	pass

def on_logout(login_manager):
	# destroys cart session on logout
	sid = frappe.local.session.get("awc_sid", frappe.local.request.cookies.get("awc_sid"))
	if sid:
		awc_sid = "awc_session_{0}".format(sid)
		frappe.cache().set_value(awc_sid, None)
