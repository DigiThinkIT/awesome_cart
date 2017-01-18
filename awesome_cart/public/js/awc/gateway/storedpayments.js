frappe.provide("awc.gateway");

awc.gateway.StoredPaymentEditor = Class.extend({
	init: function($el) {
		var scope = this;
		this.$el = $el;
		this.primary_field = $el.attr('data-primary-field');
		this.$content = $el.find('.content');
		this.prefix = $el.attr('data-field-prefix');
		this.$reditor = new awc.RadioEditor($el.find('.awc-radio-editor'), null, this.formatter.bind(this), "");
		this.$reditor.$el.on('option-select option-edit option-remove', 
			function(e, value, record, mode) {

				if ( mode == 'select' ) {

				} else if ( mode == 'edit' ) {

				} else if ( mode == 'remove' ) {

				}
			});

		// trigger fetching data after page load
		$(function() { scope.$reditor.update(); });
	},

	update: function() {
		this.$reditor.update();
	},

	formatter: function(r) {
		return {
			selected: r[this.primary_field],
			value: r.name,
			label: r.label,
			detail: '<div><pre>' + r.payment_detail + '</pre>' +
				'<address>' +
					(r.address.address_line1?r.address_line1 + '<br>':'') +
					(r.address.address_line2?r.address_line2 + '<br>':'') +
					((r.address.city || r.address.state || r.address.pincode)?(r.address.city?r.address.city + ', ':'') + (r.address.state?r.address.state + ' ':'') + r.address.pincode + '<br>':'') +
					r.address.country +
                                '</address></div>'
		};
	}

});
