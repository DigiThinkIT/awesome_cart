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

# keep track of country->region field changes
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "=", "Country"],
			["fieldname", "=", "region"]
		]
	}
]

#update_website_context = "awesome_cart.utils.update_context"
web_include_js = [
	"https://www.promisejs.org/polyfills/promise-7.0.4.min.js",
	"/assets/awesome_cart/js/client/awc.standalone.js",
	"/assets/awesome_cart/js/client/awc.erpnext.adapter.js",
	"/assets/js/awesome_cart.js"
]

# page prerender override to generate guest users
on_render_page = [ "awesome_cart.utils.on_render_page" ]

website_route_rules = [
	{ "from_route": "/cart_success/<path:so_name>", "to_route": "cart_success" },
	{ "from_route": "/awc_template/<name>", "to_route": "awc_template" },
	{ "from_route": "/p/<name>", "to_route": "awc_product" }
]

# cart context override
extend_website_page_controller_context = {
	"erpnext.templates.pages.cart": "awesome_cart.templates.pages.cart"
}

doc_events = {
	"Payment Request": {
		"get_payment_url": "awesome_cart.utils.get_payment_url"
	},
	"Shopping Cart Settings": {
		"validate": "awesome_cart.utils.validate_price_list_currency"
	}
}

awc_shipping_api = {
	"get_rates": "awesome_cart.dummy.get_shipping_rates"
}
