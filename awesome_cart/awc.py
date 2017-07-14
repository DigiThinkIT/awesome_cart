from __future__ import unicode_literals

import json
import traceback
import frappe
from frappe import _dict
from frappe.utils import cint, cstr, random_string, flt
from erpnext.stock.get_item_details import apply_price_list_on_item
from erpnext.shopping_cart.product import get_product_info

from compat.customer import get_current_customer
from compat.shopping_cart import apply_cart_settings, set_taxes, get_cart_quotation
from compat.erpnext.shopping_cart import get_shopping_cart_settings, get_pricing_rule_for_item
from .dbug import pretty_json, log

def get_user_quotation(awc_session):
	party = None
	if awc_session.get("selected_customer"):
		party = frappe.get_doc("Customer", awc_session["selected_customer"])

	return get_cart_quotation(party=party)

def find_index(arr, fn):
	for i, item in enumerate(arr):
		if fn(item):
			return i
	return -1

def find_indexes(arr, fn):
	results = []
	for i, item in enumerate(arr):
		if fn(item):
			results.append(i)

	return results

def get_template(tpl_name):
	"""Get the template by name"""
	if tpl_name and frappe.db.exists("AWC Template", tpl_name):
	   tpl = frappe.get_doc("AWC Template", tpl_name)
	   return tpl.get("template_body", "")

	return ""

def is_logged_in():
	session_user = frappe.get_user()

	if session_user.name == "Guest":
		return False

	return True

def get_price(item_code, price_list=None, qty=1, find_price_list=False):

	customer = get_current_customer()
	awc_session = get_awc_session()
	if awc_session.get("selected_customer"):
		customer = frappe.get_doc("Custoemr", awc_session.get("selected_customer"))

	if not price_list and find_price_list and is_logged_in():
		quotation = _get_cart_quotation()
		price_list = quotation.get("selling_price_list")

	if price_list:
		cart_settings = get_shopping_cart_settings()
		template_item_code = frappe.db.get_value("Item", item_code, "variant_of")

		price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
			filters={"price_list": price_list, "item_code": item_code})

		if not price and template_item_code:
			price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
				filters={"price_list": price_list, "item_code": template_item_code})

		if price:

			rule_query = {
				"item_code": item_code,
				"qty": qty,
				"transaction_type": "selling",
				"price_list": price_list,
				"customer_group": customer.customer_group,
				"company": cart_settings.company,
				"conversion_rate": 1,
				"for_shopping_cart": True
			}

			pricing_rule = get_pricing_rule_for_item(frappe._dict(rule_query))
			price_list_rate = price[0].price_list_rate

			if pricing_rule:
				if pricing_rule.pricing_rule_for == "Discount Percentage":
					price[0].price_list_rate = flt(price[0].price_list_rate * (1.0 - (pricing_rule.discount_percentage / 100.0)))

				if pricing_rule.pricing_rule_for == "Price":
					price[0].price_list_rate = pricing_rule.price_list_rate

			return {
				"base_price_rate": price_list_rate,
				"currency": price[0].get("currency"),
				"rate": price[0].get("price_list_rate")}

	return {
			"base_price_rate": frappe.db.get_value("Item", item_code, "standard_rate"),
			"currency": "", #TODO: get default currency, don't remember from where atm
			"rate": frappe.db.get_value("Item", item_code, "standard_rate")
		}

def get_awc_item_by_route(route):
	"""Retrieves awc item by its route"""
	# Get awc item name through a get_list and filter call
	# then query the actual doctype with name.
	# NOTE: Is there a less convoluted way of searching doctypes and getting
	#       it's doctype instance?
	awc_item = frappe.get_list("AWC Item", fields="name", filters = {"product_route": route}, ignore_permissions=1)
	if len(awc_item) == 0:
		return None, None

	awc_item = frappe.get_doc("AWC Item", awc_item[0].name)

	# Finally get the item associated with this AWC item
	item = frappe.get_doc("Item", awc_item.product_name)

	# return both as they are usually used together
	return (awc_item, item)

def get_awc_item_custom_data(name):
	"""Returns a dictionary of custom key/values in the awc item"""
	if isinstance(name, str) or isinstance(name, unicode):
		awc_item = frappe.get_doc("AWC Item", name)
	else:
		awc_item = name

	custom_data = {}
	for custom in awc_item.get("custom_data"):
		custom_data[custom.key] = custom.value

	return custom_data

def build_awc_options_from_varients(item):

	item = frappe.get_doc("Item", item.name)

	# early exit for items which are already variants to another item
	if item.get('variant_of'):
		return {'variants': [], 'hashes': {}}

	context = _dict()
	context = item.get_context(context)

	options = {'variants': [], 'hashes': {}}
	if item.get('has_variants'):

		for att in item.get('attributes'):
			attribute = frappe.get_doc('Item Attribute', att.get('attribute'))

			values = context.get('attribute_values')[attribute.attribute_name]

			options['variants'].append({
				'id': attribute.name,
				'label': attribute.attribute_name,
				'values': values,
				'default': context.get('selected_attributes').get(attribute.name)
			})

		for variant in context.get('variants'):
			tmp_atts = dict()
			for att in variant.get('attributes', []):
				att_name = att.get('attribute')
				att_value = att.get('attribute_value')
				tmp_atts[att_name] = att_value

			opt_hash = []
			for opt_variant in options['variants']:
				opt_hash.append(tmp_atts.get(opt_variant.get('id')))


			options["hashes"][",".join(opt_hash)] = variant.get('name')

	return options

def get_content_sections(awc_item):
	"""Returns and groups content by it's leading section"""
	sections = []
	section = None
	for content in awc_item.get("product_content"):
		if content.data_type == "Section Break":
			# when we find a section add last section to section list
			if section:
				sections.append(section)

			# fill out section values
			section = { "content": [], "background_image_url": content.get("background_image_url") }

		else:
			# create section object if none are set. This makes it a default section
			if not section:
				section = { "content": [] }

			# by default we should always expect at least one content piece
			section_content = { "html": [content.data_content_1] }

			# check if we want more than one content pice
			if cint(content.data_content_count) > 1:
				# then add it to our content array
				section_content["html"].append(content.data_content_2)

			# finally add this content object to the section
			section["content"].append(section_content)

	# if we have one section left, add it to the sections list
	if section:
		sections.append(section)

	return sections

def _get_cart_quotation(awc_session=None):
	if not awc_session:
		awc_session = get_awc_session()

	cart_info = get_user_quotation(awc_session)
	return cart_info.get('doc')

@frappe.whitelist(allow_guest=True, xss_safe=True)
def get_product_by_sku(sku, detailed=0, awc_session=None):
	"""Get's product in awcjs format by its sku and optionally detailed data."""

	price_list = None
	if is_logged_in():
		quotation = _get_cart_quotation()
		price_list = quotation.get("selling_price_list")

	# fetch item by its sku/item_code
	item = frappe.get_list("Item", fields="*", filters = {"item_code": sku}, ignore_permissions=1)

	if not item or len(item) == 0:
		return { "success": False, "data": None }

	item = item[0]

	if item.disabled:
		return { "success": False, "data": None }

	# get awc item name by its item link
	awc_item = frappe.get_list("AWC Item", fields="*", filters = {"product_name": item.name}, ignore_permissions=1)

	missing_awc_item = False
	# lets check if we have an AWC Item for this Item
	if not awc_item or len(awc_item) == 0:
		# if not, lets check if we have an AWC Item for its variant_of value if set
		if item.get('variant_of'):
			awc_item = frappe.get_list("AWC Item", fields="*", filters = {"product_name": item.variant_of}, ignore_permissions=1)
			if not awc_item or len(awc_item) == 0:
				missing_awc_item = "{0}(Parent), {1}(Variant)".format(item.variant_of, item.name)
		else:
			missing_awc_item = item.name

	if missing_awc_item:
		return { "success": False, "data": None, "error": "Missing AWC Item for {0}".format(missing_awc_item) }

	# finally get awc_item doctype instance
	awc_item = frappe.get_doc("AWC Item", awc_item[0].name)
	# get awc_item custom data as dictionary
	custom_data = get_awc_item_custom_data(awc_item)

	price_info = get_price(item.get("item_code"), price_list)
	price = price_info.get("rate")

	variants = frappe.get_all("Item", fields=["name", "item_code"], filters={"variant_of": item.get("name")})
	for vitem in variants:
		vprice = get_price(vitem.get("item_code"), price_list).get("rate")
		if vprice < price:
			price = vprice

	# format product for awcjs
	product = dict(
		sku=item.item_code,
		name=item.item_name,
		custom=custom_data,
		weight=item.get("net_weight", 0),
		warehouse=item.get("default_warehouse"),
		description=awc_item.description_short,
		imageUrl=awc_item.product_thumbnail,
		productUrl="/p/%s" % awc_item.product_route,
		base_price=price_info.get("base_price_rate"),
		price=price,
		listing_widget=awc_item.listing_widget,
		product_widget=awc_item.product_widget,
		product_template=awc_item.product_template,
		options=build_awc_options_from_varients(item),
		tags=awc_item.tags.split(',') if awc_item.tags else []
	)

	# append detailed information only if required
	if detailed:
		product["detail"] = dict(
			description_short=awc_item.description_short,
			description_long=awc_item.description_long,
			sections=get_content_sections(awc_item)
		)

	return { "success": True, "data": product }

@frappe.whitelist(allow_guest=True, xss_safe=True)
def fetch_products(tags="", terms="", order_by="order_weight", order_dir="asc", start=0, limit=None):
	"""Fetches a list of products filtered by tags"""

	payload = {
		"success": False
	}
	try:
		price_list = None
		if is_logged_in():
			quotation = _get_cart_quotation()
			price_list = quotation.get("selling_price_list")

		tags = tags.split(',')  # split tag string into list
		# Convert order_by and order_dir values to acceptable values or defaults
		order_by_clean = dict(weight="order_weight").get(order_by if order_by else "", "order_weight")
		order_dir_clean = dict(asc="asc", desc="desc").get(order_dir if order_dir else "", "asc")

		# builds the WHERE part of the sql query to match tags by AND/OR binary matches
		# matches are grouped into groups of AND matches with extra groups being OR
		# example:
		# ( tagmatch AND tagmatch AND tagmatch ) OR ( tagmatch AND tagmatch AND tagmatch )
		tags_match = []
		tag_group = []
		for tag in tags:
			if tag:
				# anything prepended with a pipe is an OR match
				if tag[0] == '|':
					if len(tag_group) > 0:
						tags_match.append(tag_group)
						tag_group = []
					tag_group.append(' a.tags REGEXP "(^|,){}(,|$)" '.format(tag[1:]))
				else: # anything else is an AND match
					tag_group.append(' a.tags REGEXP "(^|,){}(,|$)" '.format(tag))

		# add any dangly groups to match list
		if len(tag_group) > 0:
			tags_match.append(tag_group)

		# build actual WHERE query part from groups
		if len(tags_match) > 0:
			tags_match = " OR ".join( \
				["({})".format(" AND ".join(group)) \
					for group in tags_match]
			)
			if tags_match:
				tags_match = "({})".format(tags_match)

		else:
			tags_match = ""

		sql_count = "SELECT count(*) \
			FROM `tabAWC Item` a\
			{};\
			".format("WHERE %s" % tags_match if tags_match else "")

		result_count = cint(frappe.db.sql(sql_count, as_list=1)[0][0])

		sql = """SELECT
			i.name,
			i.item_code,
			i.item_name,
			i.has_variants,
			i.standard_rate,
			i.net_weight,
			a.name as awc_item_name,
			a.product_route as awc_product_route,
			a.description_short as awc_description_short,
			a.description_long as awc_description_long,
			a.listing_widget as awc_listing_widget,
			a.product_widget as awc_product_widget,
			a.product_template as awc_product_template,
			a.product_thumbnail as awc_product_thumbnail,
			a.slider as awc_slider,
			a.tags as awc_tags
			FROM `tabAWC Item` a, `tabItem` i
			WHERE i.name = a.product_name
			AND a.catalog_visible = 1 and i.disabled != 1
			{}
			ORDER BY {} {}
			{}""".format(
				"AND %s" % tags_match if tags_match else "",
				order_by_clean,
				order_dir_clean,
				"LIMIT {}, {}".format(
					int(start),
					int(limit)) if limit != None else ""
				)

		result = frappe.db.sql(sql, as_dict=1)

		products = []
		for item in result:
			price_info = get_price(item.get("item_code"), price_list)
			price = price_info.get("rate")

			variants = frappe.get_all("Item", fields=["name", "item_code"], filters={"variant_of": item.get("name")})
			for vitem in variants:
				vprice = get_price(vitem.get("item_code"), price_list).get("rate")
				if vprice < price:
					price = vprice

			product = dict(
				sku=item.item_code,
				name=item.item_name,
				weight=item.get("net_weight", 0),
				custom=get_awc_item_custom_data(item.awc_item_name),
				productUrl="/p/%s" % item.awc_product_route,
				description=item.awc_description_short,
				imageUrl=item.awc_product_thumbnail,
				base_price=price_info.get("base_price_rate") ,
				price=price,
				listing_widget=item.awc_listing_widget,
				product_widget=item.awc_product_widget,
				product_template=item.awc_product_template,
				options=build_awc_options_from_varients(item),
				tags=item.awc_tags.split(',') if item.awc_tags else []
			)
			products.append(product)

		payload["success"] = True
		payload["total_records"] = result_count
		payload["data"] = products
	except Exception as ex:
		log("ERROR")
		payload["success"] = False
		payload["message"] = traceback.format_exc(ex)
		log(payload["message"])

	return payload

def collect_totals(quotation, awc, awc_session):
	if quotation:
		quotation.run_method("calculate_taxes_and_totals")
		awc["totals"]["sub_total"] = quotation.get("total")
		awc["totals"]["grand_total"] = quotation.get("grand_total")
		#if "other" not in awc["totals"]:
		awc["totals"]["other"] = []

		for tax in quotation.get("taxes"):
			total_entry = next((x for x in awc["totals"]["other"] if x.get("name") == tax.get("description")), None)
			if not total_entry:
				total_entry = { "name": tax.get("description"), "label": tax.get("description"), "value": tax.get("tax_amount")}
				awc["totals"]["other"].append(total_entry)

			total_entry["value"] = tax.get("tax_amount")

		# dumb tax sorting by names
		tax_order = {"Sales Tax": -1000, "Shipping": -500}
		awc["totals"]["other"].sort(key=lambda x: next((v for k,v in tax_order.items() if x["name"].startswith(k)), 1000))

	else:
		awc["totals"]["sub_total"] = 0
		awc["totals"]["grand_total"] = 0
		for awc_item in awc["items"]:
			product = get_product_by_sku(awc_item.get("sku"))
			if product.get('success'):
				product_total = product["data"].get("price") * cint(awc_item.get("qty"))
				if awc_item.get("options", {}).get("custom", {}).get("rate"):
					product_total = flt(awc_item["options"]["custom"]["rate"]) * cint(awc_item.get("qty"))
				awc["totals"]["sub_total"] = awc["totals"]["sub_total"] + product_total

		awc["totals"]["grand_total"] = awc["totals"]["sub_total"] + awc["totals"].get("shipping_total", 0)

def get_awc_session():
	# get session id from request
	sid = frappe.local.session.get("awc_sid", frappe.local.request.cookies.get("awc_sid"))
	if sid:
		awc_sid = "awc_session_{0}".format(sid)
	awc_session = None

	pretty_json(awc_session)

	# lets make sure IPs match before applying this sid
	if sid != None:
		awc_session = frappe.cache().get_value(awc_sid)
		if awc_session:
			if awc_session.get("session_ip") != frappe.local.request_ip:
				# IP do not match... force build session from scratch
				sid = None
				awc_sid = None
				awc_session = None

	if awc_session is None:
		if not sid:
			sid = random_string(64)
			awc_sid = "awc_session_{0}".format(sid)

		awc_session = {
			"session_ip": frappe.local.request_ip,
			"cart": { "items": [], "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }
		}

		frappe.cache().set_value(awc_sid, awc_session)
	else:
		# update old session structures
		if not awc_session.get("cart"):
			awc_session["cart"] = { "items": [], "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }

		if not awc_session["cart"].get("totals"):
			awc_session["cart"]["totals"] = { "sub_total": 0, "grand_total": 0, "other": [] }

		if not awc_session["cart"]["totals"].get("other"):
			awc_session["cart"]["totals"]["other"] = []

	frappe.local.session["awc_sid"] = sid
	frappe.local.cookie_manager.set_cookie("awc_sid", frappe.local.session["awc_sid"] )

	return awc_session

def set_awc_session(session):
	awc_session = get_awc_session()
	frappe.cache().set_value("awc_session_{0}".format(frappe.local.session["awc_sid"]), session)
	return session

def clear_awc_session():
	awc_session = get_awc_session()
	del awc_session["shipping_method"]
	del awc_session["shipping_rates"]
	del awc_session["shipping_rates_list"]
	awc_session["cart"] = { "items": [], "totals": { "sub_total": 0, "grand_total": 0, "other": [] } }
	return set_awc_session(awc_session)

def sync_awc_and_quotation(awc_session, quotation, quotation_is_dirty=False):
	# convert quotation to awc object
	# and merge items in the case where items are added before logging in.

	# steps:
	# 1) loop over all awc items and update quotation items matching names/ids
	# 2) remove invalid awc items who's skus do not match any products(awc items)
	# 3) loop over remaining unmatched quotation items and create awc items
	# 4) remove invalid quotation items who's skus do not match any products(awc items)
	awc = awc_session.get("cart")

	if not awc:
		# abnormal, there should be a cart instance on the session
		log(awc_session, trace=1)

	awc_is_dirty = False
	awc_items_to_remove = []
	awc_items_matched = []
	# step 1
	# iterate over all awc items and update quotation to match values
	awc_items = awc.get("items", [])
	for awc_idx in range(0, len(awc_items)):
		awc_item = awc_items[awc_idx]
		product = get_product_by_sku(awc_item.get("sku"))

		if awc_item.get("id"):
			idx = find_index(quotation.get("items", []), lambda itm: itm.get("name") == awc_item.get("id"))
			if idx > -1:
				item = quotation.items[idx]
				# make sure product exists
				if product.get("success"):
					product = product.get("data")
					if item.qty != awc_item.get("qty"):
						item.qty = awc_item.get("qty")
						quotation_is_dirty = True

					if item.item_code != awc_item.get("sku"):
						item.item_code = awc_item.get("sku")
						quotation_is_dirty = True

					if item.awc_group != awc_item.get('options', {}).get('group'):
						item.awc_group = awc_item.get('options', {}).get('group')
						quotation_is_dirty = True

					if item.awc_subgroup != awc_item.get('options', {}).get('subgroup'):
						item.awc_subgroup = awc_item.get('options', {}).get('subgroup')
						quotation_is_dirty = True

					if item.awc_group_label != awc_item.get('options', {}).get('label'):
						item.awc_group_label = awc_item.get('options', {}).get('label')
						quotation_is_dirty = True

					if item.description != awc_item.get("options", {}).get("description", item.description):
						item.description = awc_item.get("options", {}).get("description")
						quotation_is_dirty = True

					if not item.image and awc_item.get("options", {}).get("image") and item.image != awc_item.get("options", {}).get("image"):
						item.image = awc_item["options"]["image"]
						quotation_is_dirty = True

					item.warehouse = product.get("warehouse")
					update_quotation_item_awc_fields(item, awc_item)

					if awc_item.get("options", {}).get("custom", {}).get("rate", None) != None:
						item.set("ignore_pricing_rule", 1)
						set_quotation_item_rate(item, awc_item["options"]["custom"]["rate"], product)
					else:
						set_quotation_item_rate(item, product.get("price"), product)
						item.set("ignore_pricing_rule", 0)

					awc_items_matched.append(awc_item.get("id"))
				else:
					# sku is invalid. Flag item to be removed from awc session
					awc_items_to_remove.append(awc_item)

			elif awc_item.get('id')[0:4] == "QUOD":
				# remove orphaned items
				awc_items_to_remove.append(awc_item)
			else:
				if product.get("success"):
					product = product.get("data")

					# no quotation item matched, so lets create one
					item_data = {
						"doctype": "Quotation Item",
						"item_code": awc_item.get("sku"),
						"item_name": product.get("name"),
						"description": awc_item.get("options", {}).get("description", product.get("name")),
						"qty": cint(awc_item.get("qty")),
						"warehouse": product.get("warehouse")
					}

					if awc_item.get("options", {}).get("image"):
						item_data["image"] = awc_item["options"]["image"]

					update_quotation_item_awc_fields(item_data, awc_item)

					new_quotation_item = quotation.append("items", item_data)

					if awc_item.get("options", {}).get("custom", {}).get("rate", None) != None:
						new_quotation_item.set("ignore_pricing_rule", 1)
						set_quotation_item_rate(new_quotation_item, awc_item["options"]["custom"]["rate"], product)
					else:
						new_quotation_item.set("ignore_pricing_rule", 0)
						set_quotation_item_rate(new_quotation_item, product.get("price"), product)

					awc_item["unit"] = new_quotation_item.rate
					awc_item["total"] = new_quotation_item.amount

					# BUGFIX: makes sure this item gets a name during login
					new_quotation_item.save()

					awc_item["id"] = new_quotation_item.name
					# make sure we won't add this new item again on step 2
					update_quotation_item_awc_fields(new_quotation_item, awc_item)
					awc_items_matched.append(awc_item.get("id"))

					quotation_is_dirty = True 	# update quotation records
					awc_is_dirty = True			# flag awc session for storage
				else:
					awc_items_to_remove.append(awc_item)
		else:
			# drop awc items if they have invalid ids
			awc_items_to_remove.append(awc_item)

	# step 2
	# remove invalid awc items
	for awc_item in awc_items_to_remove:
		idx = awc["items"].index(awc_item)
		del awc["items"][idx]
		awc_is_dirty = True

	quotation_item_to_remove = []

	# step 3
	# now create awc items for quotation items not matched with existing awc session
	for item in [qitem for qitem in quotation.get("items", []) \
		if qitem.name not in awc_items_matched]:

		product = get_product_by_sku(item.get("item_code"))
		if product.get("success"):
			product = product.get("data")
			awc_item = {
				"id": item.name,
				"sku": item.item_code,
				"qty": cint(item.qty),
				"warehouse": product.get("warehouse"),
				"unit": item.rate,
				"total": item.amount,
				"image": item.image,
				"base_price": product.get("base_price"),
				"options": {
					"description": item.description
				}
			}

			if item.awc_group:
				awc_item["options"].update({
					"group": item.awc_group,
					"subgroup": item.awc_subgroup,
					"label": item.awc_group_label,
					"image": item.image
				})

				if awc_item["base_price"] != awc_item["unit"]:
					awc_item["options"]["custom"] = {
						"rate": item.rate
					}

			awc["items"].append(awc_item)
			awc_is_dirty = True
		else:
			quotation_item_to_remove.append(item)

	# step 4
	# remove invalid quotation items
	for item in quotation_item_to_remove:
		idx = quotation.items.index(item)
		del quotation.items[idx]
		quotation_is_dirty = True


	if quotation_is_dirty:
		update_cart_settings(quotation, awc_session)
		quotation.flags.ignore_permissions = True
		quotation.save()
		frappe.db.commit()

	collect_totals(quotation, awc, awc_session)

	if awc_is_dirty:
		set_awc_session(awc_session)

def update_shipping_quotation(quotation, awc_session):
	"""NOTE: this method has to be called after calling apply_cart_settings()
	due to tax rules dumping all existing taxes every time they update."""

	# if we have shipping rates and a selected rate, update or create shipping tax
	if awc_session.get("shipping_method"):
		rate = awc_session.get("shipping_method")
		if rate:
			shipping_tax = {
				"tax_amount": rate.get("fee"),
				"description": "Shipping ("+rate.get("name")+")",
				"charge_type": "Actual",
				"account_head": frappe.get_value("Awc Settings", "Awc Settings", "shipping_account"),
			}

			quotation.append("taxes", shipping_tax)

		return True

	return False

def set_field(obj, field, value):
	if isinstance(obj, dict):
		obj[field] = value
	else:
		obj.set(field, value)

def set_quotation_item_rate(quotation_item, rate, product):
	quotation_item.discount_percentage = 100 - flt(rate * 100) / flt(product.get("base_price"))
	quotation_item.rate = flt(rate)
	quotation_item.price_list_rate = flt(product.get("base_price"))
	quotation_item.amount = flt(rate) * quotation_item.qty
	quotation_item.base_price_list_rate = flt(product.get("base_price"))
	quotation_item.base_rate = flt(product.get("base_price"))

def update_quotation_item_awc_fields(quotation_item, awc_item):
	if awc_item.get('options'):
		set_field(quotation_item, 'awc_group', awc_item['options'].get('group'))
		set_field(quotation_item, 'awc_subgroup', awc_item['options'].get('subgroup'))
		set_field(quotation_item, 'awc_group_label', awc_item['options'].get('label'))
		if awc_item['options'].get('description'):
			set_field(quotation_item, 'description', awc_item['options'].get('description'))

		if awc_item['options'].get('image'):
			set_field(quotation_item, 'image', awc_item['options'].get('image'))

		if awc_item['options'].get('custom'):
			for field, value in awc_item['options']['custom'].items():
				set_field(quotation_item, field, value)

def remove_from_cart(items_to_remove, cart_items):
	success = False
	removed_ids = []

	awc_items = list(cart_items)

	for rm_item in items_to_remove:
		item_id = rm_item.get("id")
		item = next((x for x in awc_items if x.get("id") == item_id), None)
		if item:
			group_name = item.get("options", {}).get("group", None)

			# remove item and related grouped items from cart
			awc_items = [ itm for itm in awc_items \
				if itm["id"] != item["id"] ]

			if group_name:
				awc_items = [ itm for itm in awc_items \
					if itm.get("options", {}).get("group") != group_name ]

			success = True

	if success:
		awc_items_id_list = [x.get("id") for x in awc_items]
		removed_ids = [itm.get("id") for itm in cart_items if itm.get("id") not in awc_items_id_list ]

	return success, removed_ids, awc_items

def update_cart_settings(quotation, awc_session):
	#apply_cart_settings(quotation=quotation)
	set_taxes(quotation, get_shopping_cart_settings())
	#quotation.run_method("calculate_taxes_and_totals")
	update_shipping_quotation(quotation, awc_session)

def reset_shipping():
	customer = get_current_customer()
	awc_session = get_awc_session()
	awc = awc_session.get("cart")
	quotation = None

	if not awc:
		awc = clear_awc_session()

	if customer:
		cart_info = get_user_quotation(awc_session)
		quotation = cart_info.get('doc')

		if len(quotation.items) == 0:
			apply_cart_settings(quotation=quotation)
		quotation.flags.ignore_permissions=True

	if quotation:
		sync_awc_and_quotation(awc_session, quotation)


	if "shipping_method" in awc_session:
		del awc_session["shipping_method"]

	if "shipping_address" in awc_session:
		del awc_session["shipping_address"]

	if "shipping_rates_list" in awc_session:
		awc_session["shipping_rates_list"] = []

	if quotation:
		update_cart_settings(quotation, awc_session)
		quotation.flags.ignore_permissions = True
		quotation.save()

		collect_totals(quotation, awc, awc_session)
	else:
		collect_totals(None, awc, awc_session)

	set_awc_session(awc_session)
	frappe.db.commit()

def calculate_shipping(rate_name, address, awc_session, quotation, save=True):
	awc = awc_session.get("cart")

	# clean up for old test data
	if "shipping_method" in awc_session and awc_session.get("shipping_method") == None:
		del awc_session["shipping_method"]

	# if no rate_name provided get last method selected
	if not rate_name:
		rate_name = awc_session.get("shipping_method", {}).get("name")

	if rate_name != awc_session.get("shipping_method", {}).get("name"):
		rate_changed = True
	else:
		rate_changed = False

	# rate selection
	rate = awc_session.get("shipping_rates", {}).get(rate_name, None)

	# if no address provided get last provided address
	if not address:
		address = awc_session.get("shipping_address")

	if address and awc_session.get("shipping_address") and \
		len(address.items()) > 0 and len(awc_session["shipping_address"].items()) > 0:

		address_field_equal = reduce((lambda x, y: x and y), [ \
			address.get(k, None) == v \
			for k,v in awc_session.get("shipping_address", {}).items() \
		])
	else:
		address_field_equal = False

	address_changed = len(address.items()) != len(awc_session.get("shipping_address", {})) or not address_field_equal

	if address and address_changed:
		awc_session["shipping_rates_list"] = update_shipping_rate(address, awc_session)

	# if we have no selection but we have shipping rates, pick first option
	if not rate and len(awc_session.get("shipping_rates_list", [])) > 0:
		rate = awc_session["shipping_rates_list"][0]

	# if no rates available, then reset shipping method
	if rate and len(awc_session.get("shipping_rates_list", [])) > 0:
		awc_session["shipping_method"] = rate
	else:
		del awc_session["shipping_method"]

	shipping_address_name = None

	if quotation:
		update_cart_settings(quotation, awc_session)
		shipping_address_name = quotation.get("shipping_address_name")
		if save:
			quotation.flags.ignore_permissions = True
			quotation.save()
			frappe.db.commit()

		collect_totals(quotation, awc, awc_session)
	else:
		collect_totals(None, awc, awc_session)

	if save:
		#log("Saving session:\n{0}", pretty_json(awc_session))
		set_awc_session(awc_session)

	return {
		"success": True,
		"data": awc["items"],
		"removed": [],
		"totals": awc.get("totals"),
		"shipping_rates":  awc_session.get("shipping_rates_list",[]),
		"shipping_address_name": shipping_address_name
	}

@frappe.whitelist(allow_guest=True, xss_safe=True)
def cart(data=None, action=None):
	if data and isinstance(data, basestring):
		data = json.loads(data)

	# make sure we can handle bulk actions
	if not isinstance(data, list):
		data = [data]

	customer = get_current_customer()
	quotation = None
	awc_session = get_awc_session()

	if customer:
		cart_info = get_user_quotation(awc_session)
		quotation = cart_info.get('doc')

		if len(quotation.items) == 0:
			apply_cart_settings(quotation=quotation)
		quotation.flags.ignore_permissions=True
		quotation.save()

	awc = awc_session.get("cart")

	if not awc:
		awc = clear_awc_session()

	if quotation:
		sync_awc_and_quotation(awc_session, quotation)

	#log(pretty_json(awc))

	if not action:
		return { "data": awc, "success": True}

	elif action == "calculate_shipping":
		rate_name = data[0].get("name")
		address = data[0].get("address")
		if address:
			address_name = address.get("shipping_address")
			if not address_name:
				new_address = frappe.new_doc("Address")
				new_address.update({
					#"address_title": data[0].get("address").get("title"),
					"address_type": data[0].get("address").get("address_type", "Shipping"),
					"customer": quotation.customer,
					"address_line1": data[0].get("address").get("address_1"),
					"address_line2": data[0].get("address").get("address_2"),
					"city": data[0].get("address").get("city"),
					"state": data[0].get("address").get("state"),
					"country": data[0].get("address").get("country"),
					"phone": data[0].get("address").get("phone"),
					"email_id": frappe.session.user,
					"pincode": data[0].get("address").get("pincode")
				})
				new_address.flags.ignore_permissions= True
				new_address.save()
				address_name = new_address.name
			quotation.shipping_address_name = address_name
			quotation.save()

		return calculate_shipping(rate_name, address, awc_session, quotation)

	elif action == "updateItem":

		# for now only qty field is updatable
		# key in awc fields and values are erpnext fields for quotation item
		valid_update_fields = {"qty": "qty"}
		remove_items = []
		removed_ids = []

		for item in data:

			awc_item = next((i for i in awc["items"] if i.get("id") == item.get("id")), None)

			if awc_item:
				quotation_item = None
				if quotation:
					quotation_item = next((q for q in quotation.get("items", []) if q.name == awc_item.get("id")), None)

				for awc_key, erp_key in valid_update_fields.iteritems():

					if awc_key in item:
						awc_item[awc_key] = item.get(awc_key)

						if awc_key == "qty":
							awc_item["total"] = awc_item["unit"] * awc_item["qty"]

						if quotation_item:
							quotation_item.set(erp_key, item.get(awc_key))

							#if erp_key == "qty":
								#quotation_item.amount = flt(quotation_item.rate) * quotation_item.qty

				if awc_item.get('options', {}).get('group'):
					# find all subgroup items and update qty accordingly
					for sub_item in [i for i in awc["items"] if i.get('options', {}).get('group') == awc_item.get('options', {}).get('group')]:
						sub_item["qty"] = awc_item["qty"]

						if quotation:
							sub_quotation_item = next((q for q in quotation.get("items", []) if q.name == sub_item.get("id")), None)
							if sub_quotation_item:
								sub_quotation_item.set("qty", sub_item.get("qty"))
								#sub_quotation_item.amount = flt(sub_quotation_item.rate) * sub_quotation_item.qty

						sub_item["total"] = sub_item["unit"] * sub_item["qty"]

				if awc_item.get("qty") == 0:
					remove_items.append(awc_item)

		# remove all 0 qty items
		if len(remove_items) > 0:
			success, removed_ids, awc_items = remove_from_cart(remove_items, awc["items"])
			if success:
				awc["items"] = awc_items

				if quotation:
					# remove item and related grouped items from quote
					quotation_items = [ itm for itm in quotation.get("items", []) \
						if itm.name not in removed_ids ]

					quotation.set("items", quotation_items)

		shipping_info = calculate_shipping(None, None, awc_session, quotation, save=0)

		if quotation:
			update_cart_settings(quotation, awc_session)
			quotation.flags.ignore_permissions = True
			quotation.save()
			frappe.db.commit()

			collect_totals(quotation, awc, awc_session)
		else:
			collect_totals(None, awc, awc_session)

		set_awc_session(awc_session)

		return {
			"success": True,
			"data": awc["items"],
			"removed": removed_ids,
			"totals": awc.get("totals"),
			"shipping_rates": shipping_info.get("shipping_rates")
		}

	elif action == "addToCart":

		for item in data:
			# need basic data validation here
			if not item.get("sku"):
				return { "success": False, "message": "Invalid Data" }

			if not item.get("qty"):
				return { "success": False, "message": "Invalid Data" }

			product = get_product_by_sku(item.get("sku")).get("data")

			if item.get("options", {}).get("custom", {}).get("rate", None) != None:
				item["total"] = flt(item["options"]["custom"]["rate"]) * item.get("qty")
				item["unit"] = flt(item["options"]["custom"]["rate"])
			else:
				item["total"] = flt(product.get("price") * item.get("qty"))
				item["unit"] = flt(product.get("price"))

			if quotation:

				item_data = {
					"doctype": "Quotation Item",
					"item_code": item.get("sku"),
					"item_name": product.get("name"),
					"description": item.get("options", {}).get("description", product.get("name")),
					"qty": cint(item.get("qty")),
					"warehouse": product.get("warehouse")
				}

				update_quotation_item_awc_fields(item_data, item)

				quotation_item = quotation.append("items", item_data)

				# TODO: ( >_<) shitty way of setting rate due to rate reset
				#       Please fix when not utterly pissed off
				if item.get("options", {}).get("custom", {}).get("rate", None) != None:
					quotation_item.set("ignore_pricing_rule", 1)
					set_quotation_item_rate(quotation_item, item["options"]["custom"]["rate"], product)
					item_data['total'] = item["options"]["custom"]["rate"] * cint(item.get("qty"))
				else:
					quotation_item.set("ignore_pricing_rule", 0)
					set_quotation_item_rate(quotation_item, product.get("price"), product)
					item_data['total'] = product.get("price") * cint(item.get("qty"))

					#quotation_item.discount_percentage = 100 - flt(item["options"]["custom"]["rate"] * 100) / flt(product.get("price"))
					#quotation_item.rate = flt(item["options"]["custom"]["rate"])
					#quotation_item.price_list_rate = flt(product.get("price"))
					#quotation_item.amount = flt(item["options"]["custom"]["rate"])
					#quotation_item.base_price_list_rate = flt(product.get("price"))
					#quotation_item.base_rate = flt(product.get("price"))

				quotation_item.save()

				item["old_id"] = item["id"]
				item["id"] = quotation_item.name

			awc["items"].append(item)

		if quotation:
			update_cart_settings(quotation, awc_session)
			quotation.flags.ignore_permissions = True
			quotation.save()

			#log("Quotation after add to cart: \n{0}", pretty_json(quotation.as_dict()))

			frappe.db.commit()

			collect_totals(quotation, awc, awc_session)
			#log("Quotation after collecting totals: \n{0}", pretty_json(quotation.as_dict()))
		else:
			collect_totals(None, awc, awc_session)

		set_awc_session(awc_session)

		#log("Awc session after add to cart: \n{0}", pretty_json(awc_session))

		return { "success": True, "data": data, "totals": awc.get("totals") }

	elif action == "removeFromCart":

		success = False
		removed_ids = []

		success, removed_ids, awc_items = remove_from_cart(data, awc["items"])

		if success:

			awc["items"] = awc_items

			if quotation:
				# remove item and related grouped items from quote
				quotation_items = [ itm for itm in quotation.get("items", []) \
					if itm.name not in removed_ids ]

				quotation.set("items", quotation_items)

				update_cart_settings(quotation, awc_session)
				quotation.flags.ignore_permissions = True
				quotation.save()
				frappe.db.commit()
				collect_totals(quotation, awc, awc_session)
			else:
				collect_totals(None, awc, awc_session)

			set_awc_session(awc_session)

			return { "success": True, "totals": awc.get("totals"), "data": awc["items"], "removed": removed_ids }

		return { "success": False, "message": "Item not found."}

	else:
		return { "success": False, "message": "Unknown Command." }

@frappe.whitelist()
def get_shipping_rate(address):

	try:
		address = json.loads(address)
	except Exception as ex:
		return []

	awc_session = get_awc_session()
	result = update_shipping_rate(address, awc_session)

	set_awc_session(awc_session)
	return result

def update_shipping_rate(address, awc_session):

	awc = awc_session.get("cart")

	shipping_rate_api = frappe.get_hooks("shipping_rate_api")[0]
	address_link = frappe.get_value("AWC Settings", "AWC Settings", "shipping_address")
	from_address = frappe.get_doc("Address", address_link)

	package_items=[]

	for item in awc["items"]:
		if not item.get("options", {}).get("subgroup"):
			package_item = {
				"item_code": item.get("sku"),
				"qty": item.get("qty")
			}
			package_items.append(package_item)

	try:
		rates = frappe.call(shipping_rate_api["module"], from_address=from_address, to_address=address, items=package_items)
		# cache quoted rates to reference later on checkout
		awc_session["shipping_address"] = address
		awc_session["shipping_rates"] = { rate.get("name"): rate for rate in rates }
		awc_session["shipping_rates_list"] = rates

	except Exception as ex:
		log(ex)
		return []

	return rates

@frappe.whitelist()
def create_transaction(gateway_service, billing_address, shipping_address, instructions=""):

	if isinstance(billing_address, basestring):
		billing_address = json.loads(billing_address)

	if isinstance(shipping_address, basestring):
		shipping_address = json.loads(shipping_address)

	result = {
		"success": False,
		"error": "Unknown Internal Error"
	}

	# fetch customer
	customer = get_current_customer()

	# fetch awc
	awc_session = get_awc_session()
	awc = awc_session.get("cart")

	# fetch current quotation
	cart_info = get_user_quotation(awc_session)
	quotation = cart_info.get('doc')


	quotation_is_dirty = False
	# assign instructions to quotation
	if instructions:
		quotation.instructions = instructions
		quotation_is_dirty = False

	# make sure quotation and awc match
	sync_awc_and_quotation(awc_session, quotation, quotation_is_dirty)

	# create awc transaction to process payments first
	# sales order and friends will be generated from this data
	data = {
		"doctype": "AWC Transaction",
		"title": "Web Order",
		"description": "Online Web Order",
		"status": "Initiated",
		"payer_name": quotation.contact_person,
		"payer_email": quotation.contact_email,
		"amount": quotation.grand_total,
		"currency": quotation.currency,
		"session": json.dumps(awc),
		"order_id": quotation.name,
		"gateway_service": gateway_service,
		"shipping_address": shipping_address.get("shipping_address"),
		"billing_address": billing_address.get("billing_address")
	}

	if shipping_address.get("ship_method"):
		# retrieve quoted charges
		rates = awc_session.get("shipping_rates")
		data["shipping_method"] = shipping_address.get("ship_method")
		if rates:
			data["shipping_fee"] = rates.get(data["shipping_method"], {}).get("fee")

	data.update({ "billing_%s" % key: value for key, value in billing_address.iteritems() })
	data.update({ "shipping_%s" % key: value for key, value in shipping_address.iteritems() })

	transaction = frappe.get_doc(data)

	transaction.flags.ignore_permissions = 1
	transaction.save()

	set_awc_session(awc_session)

	frappe.db.commit()

	# check AWCTransaction.on_payment_authorized implementation which is
	# where this transaction continues when payment processing kicks in

	# fetch only payment request info
	result["data"] = { key: transaction.get(key) for key in \
					('amount', 'currency', 'order_id', 'title', \
					 'description', 'payer_email', 'payer_name')}

	result["data"]["reference_doctype"] = "AWC Transaction"
	result["data"]["reference_docname"] = transaction.name
	result["success"] = True
	del result["error"]

	return result
