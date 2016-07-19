# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "awesome_cart"
app_title = "Awesome Cart"
app_publisher = "DigitThinkIt, Inc."
app_description = "A one page checkout experience cart replacement for ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "forellana@digithinkit.com"
app_license = "GPL-v3"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/awesome_cart/css/awesome_cart.css"
# app_include_js = "/assets/awesome_cart/js/awesome_cart.js"

# include js, css files in header of web template
# web_include_css = "/assets/awesome_cart/css/awesome_cart.css"
# web_include_js = "/assets/awesome_cart/js/awesome_cart.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "awesome_cart.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "awesome_cart.install.before_install"
# after_install = "awesome_cart.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "awesome_cart.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"awesome_cart.tasks.all"
# 	],
# 	"daily": [
# 		"awesome_cart.tasks.daily"
# 	],
# 	"hourly": [
# 		"awesome_cart.tasks.hourly"
# 	],
# 	"weekly": [
# 		"awesome_cart.tasks.weekly"
# 	]
# 	"monthly": [
# 		"awesome_cart.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "awesome_cart.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "awesome_cart.event.get_events"
# }

