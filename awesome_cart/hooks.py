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


integration_services = ["Credit Gateway"]
#update_website_context = "awesome_cart.utils.update_context"
web_include_js = [
	"/assets/js/awc_utils.js?v=%s" % app_version,
	# polyfills for browser compatibility
	"https://www.promisejs.org/polyfills/promise-7.0.4.min.js",
	"/assets/awesome_cart/js/jquery/jquery.helpers.js?v=%s" % app_version,
	"/assets/awesome_cart/js/client/awc.standalone.js?v=%s" % app_version,
	"/assets/awesome_cart/js/client/awc.erpnext.adapter.js?v=%s" % app_version,
	"/assets/awesome_cart/js/lib/slick.min.js?v=%s" % app_version,
	"/assets/awesome_cart/js/lib/slick.auto.js?v=%s" % app_version
]

web_include_css = [
    "/assets/awesome_cart/css/slick.css?v=%s" % app_version,
    "/assets/awesome_cart/css/slick-theme.css?v=%s" % app_version,
   	"/assets/css/awc_cart.css?v=%s" % app_version,
   	"/assets/awesome_cart/css/product-detail.css?v=%s" % app_version
]

app_include_css = [
	"/assets/css/awc.ui.desk.css?v=%s" % app_version,
	"/assets/css/awc_cart.css?v=%s" % app_version
]
app_include_js = [
	"/assets/js/awc.ui.desk.js?v=%s" % app_version,
	"/assets/js/awc_utils.js?v=%s" % app_version,
	"/assets/js/credit_gateway_settings.js?v=%s" % app_version,
	"/assets/awesome_cart/js/desk_customizations/item_ignore_pricing_rule_patch.js?v=%s" % app_version
]

website_route_rules = [
	{ "from_route": "/cart_success/<path:so_name>", "to_route": "cart_success" },
	{ "from_route": "/awc_template/<name>", "to_route": "awc_template" },
	{ "from_route": "/p/<name>", "to_route": "awc_product" },
	{ "from_route": "/p/<name>/<unique>", "to_route": "awc_product" },
	{ "from_route": "/integrations/credit_gateway_checkout/<name>", "to_route": "integrations/credit_gateway_checkout" }
]

doc_events = {
	"Quotation": {
		"validate": ["awesome_cart.utils.quotation_validate"]
	},
	"Sales Order": {
		"validate": ["awesome_cart.utils.quotation_validate"]
	},
	"Sales Invoice": {
		"validate": ["awesome_cart.utils.quotation_validate"]
	},
	"Item": {
		"on_update": ["awesome_cart.utils.clear_cache_on_doc_update"]
	}
}

scheduler_events = {
	"daily_long": [
		"awesome_cart.utils.remove_expired_coupons"
	],
}

on_calculate_taxes_and_totals = "awesome_cart.utils.on_calculate_taxes_and_totals"

# cart context override
extend_website_page_controller_context = {
	"erpnext.templates.pages.cart": "awesome_cart.templates.pages.cart"
}

#on_session_creation = "awesome_cart.utils.on_session_creation"
on_logout = "awesome_cart.utils.on_logout"


awc_shipping_api = {
	"get_rates": "awesome_cart.dummy.get_shipping_rates"
}

boot_session = "awesome_cart.utils.boot_session"
update_website_context = "awesome_cart.utils.run_hotpatch"
on_session_creation = "awesome_cart.utils.run_hotpatch"
on_login = "awesome_cart.utils.run_hotpatch"
