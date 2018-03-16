frappe.provide("awc");

awc.ignore_pricing_rule_patch = {

	rate: function(frm, cdt, cdn) {
		// if user changes rate(deletes or sets) we always want to ignore rule as it is
		// an explicit value set by the user.
		frappe.model.set_value(cdt, cdn, "item_ignore_pricing_rule", 1);
		frm.refresh()
	},

	discount_percentage: function(frm, cdt, cdn) {
		var discount_percentage = frappe.model.get_value(cdt, cdn, "discount_percentage");
		// when user deletes discount_percentage we get null, so lets remove the ignore price rule to allow
		// default behaviour to take place
		if ( discount_percentage == null ) {
			frappe.model.set_value(cdt, cdn, "item_ignore_pricing_rule", 0);
		} else {
			// on a non null value passed set the ignore pricing rule as the user WANTED to
			// modify the rate value reguardless of pricing rule.
			frappe.model.set_value(cdt, cdn, "item_ignore_pricing_rule", 1);
		}
		frm.refresh();
	}

}

frappe.ui.form.on('Quotation Item', awc.ignore_pricing_rule_patch);
frappe.ui.form.on('Sales Order Item', awc.ignore_pricing_rule_patch);
frappe.ui.form.on('Sales Invoice Item', awc.ignore_pricing_rule_patch);
