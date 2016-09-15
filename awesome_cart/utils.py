# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import os

import frappe
import traceback
from frappe.utils import random_string
from .dbug import log, json_default

def on_render_page(path):
        log("-- on render_page(%s)" % path)
        try:
            filepath, ext = os.path.splitext(path)
            # we only care about pages
            if ext not in [".js", ".css"]:
                user = frappe.get_user()
                if user.name == "Guest":
                    rnd = random_string(20)
                    email = rnd + "@guest.local"
                    user = frappe.get_doc({
                        "doctype": "User",
                        "email": email,
                        "first_name": rnd,
                        "enabled": 1,
                        "new_password": random_string(10),
                        "user_type": "Website User"
                    })
                    user.flags.ignore_permissions = True
                    user.insert()
                    frappe.local.login_manager.login_as(user.name)
                    frappe.set_user(user.name)

                log("USER: %s" % user.name)
	except Exception as exp:
		log(traceback.format_exc())


def update_context(context):

	path = frappe.local.request.path[1:]
	log("Path: %s" % frappe.local.request.path)

	context.current_date = ''

	#if path == 'cart':
	#	from .templates.pages import cart
	#	cart.get_context(context)
	#
	#	log("Context for: \n%s" % json.dumps(context, indent=2, default=json_default))

class DictCopy:
	def __init__(src, dst):
		self.src = src
		self.dst = dst

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.src = None
		self.dst = None

	def copy(src_key, dst_key=None):
		if dst_key is None:
			src_key = dst_key

		if src_key in self.src:
			self.dst[dst_key] = self.src[src_key]
