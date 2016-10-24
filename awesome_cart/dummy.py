# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe

def get_shipping_rates(items, address):
	return [
		{ "label": "Dummy NextDay", "fee": 5.0, "id": "dummy-nextday", "carrier": "Dummy" },
		{ "label": "Dummy NextHour", "fee": 50.0, "id": "dummy-nexthour", "carrier": "Dummy" },
		{ "label": "Dummy NextMinute", "fee": 500.0, "id": "dummy-nextminute", "carrier": "Dummy" },
		{ "label": "Dummy NextSecond", "fee": 5000.0, "id": "dummy-nextsecond", "carrier": "Dummy" }
	]
