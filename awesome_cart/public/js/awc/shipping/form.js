frappe.provide("awc.shipping");

awc.shipping.Form = awc.Form.extend({
	init: function($form) {
		this._super($form);
	},
	
	on_validate: function() {
		return false;
	}
});

awc.shipping.init = function($container) {
	// initialize form
	$container.find('.dti-form').each(function() {
		new awc.shipping.Form($(this));
	});
}



