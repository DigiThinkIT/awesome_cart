# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from frappe.utils import random_string
from .dbug import log, json_default
from . import monkey

import frappe
import frappe.website.render

import traceback
import json
import os

__version__ = '0.0.1'

try:
    from erpnext.templates.pages import cart as exrnext_cart
    from .templates.pages import cart


    log("-- Attempting to monkey patch ---")

    def x_render_page(path):
        log("-- on render_page(%s)" % path)
        try:
            filepath, ext = os.path.splitext(path)
            # we only care about pages
            if ext not in [".js", ".css"]:
                user = frappe.get_user()
                if user.name == "Guest":
                    email = random_string(20) + "@guest.local"
                    user = frappe.get_doc({
                        "doctype": "User",
                        "email": email,
                        "first_name": "Guest User",
                        "enabled": 1,
                        "new_password": random_string(10),
                        "user_type": "Website User"
                    })
                    user.flags.ignore_permissions = True
                    user.insert()
                    frappe.local.login_manager.login_as(user.name)
                    frappe.set_user(user.name)

                log("USER: %s" % user.name)

            result = x_render_page.patched_method(path)
        except Exception as ex:
            log(traceback.format_exc())
            raise ex
        #log(result[0:40] + "...")
        return result

    # monkey patch frappe render_page so we may modify environment
    monkey.patch_method(frappe.website.render, "render_page", x_render_page)

    # monkey patch erpnext cart get_context with our version so we may modify cart
    monkey.patch_method(erpnext_cart, "get_context", cart.get_context)

except Exception as ex:
    log(traceback.format_exc())

