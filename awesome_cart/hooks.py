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

update_website_context = "awesome_cart.utils.update_context"
web_include_js = [ "/assets/js/awesome_cart.js" ]

on_render_page = [ "awesome_cart.utils.on_render_page" ]

extend_controller_context = {
	"erpnext.templates.pages.cart": "awesome_cart.templates.pages.cart"
}
