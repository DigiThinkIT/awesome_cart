from __future__ import unicode_literals

import frappe
from frappe import throw, _

from erpnext.shopping_cart.cart import get_party, get_cart_quotation, \
	apply_cart_settings, set_taxes, get_address_docs, \
	get_applicable_shipping_rules, decorate_quotation_doc, \
	get_shopping_cart_settings
from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings \
	import is_cart_enabled, get_shopping_cart_settings
from erpnext.accounts.doctype.pricing_rule.pricing_rule import get_pricing_rule_for_item
