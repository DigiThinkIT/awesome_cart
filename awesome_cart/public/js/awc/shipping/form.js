frappe.provide("awc.shipping");

awc.shipping.Form = awc.Form.extend({
	init: function($form, $carriers) {
		this.$carriers = $carriers;
		this.$carriers.hide();
		this._skip_rate_fetch = false;
		this._super($form);
	},

	get_address_fields: function() {
		return this.get_fields();	
	},

	on_validate: function(result) {

		// if form is locked(due to fetching rates), then fail validation
		if ( this._is_locked ) {
			result.valid = false;
			return result;
		}

		var scope = this;
		// only fetch rates if form is valid
		if ( result.valid && !this._skip_rate_fetch ) {
			this.lock_fields(); // lock form during rate fetching.
			this._skip_rate_fetch = true;
			frappe.call({
				method: "awesome_cart.embed.get_shipping_rates",
				args: {
					"address": this.get_address_fields(),
				},
				callback: function(r) {
					scope.lock_fields(false);
					var result = r.message;
					try {
						if ( result.success ) {
							scope.$carriers.stop().slideDown('fast');
							scope.update_rates(result.rates);
							scope.validate();
						}
					} finally {
						this._skip_rate_fetch = false;
					}
				}
			});
			this.$carriers.stop().slideUp('fast');

			result.valid = false;
		}

		return result;
	},

	update_rates: function(rates) {
		var scope = this;
		scope.$carriers.empty();

		$.each(rates, function(i, item) {
			var $choice = $(
				'<div class="field" data-label="Shipping Method">'+
					'<input class="awi" id="'+item.id+'" name="ship_carrier" type="radio" value="'+item.id+'" data-human-value="'+item.label+'">'+
					'<label for="'+item.id+'" class="visible">'+item.currency + ' ' +item.label+'</label>'+
				'</div>');
			scope.$carriers.append($choice);
			if ( i == 0 ) {
				$choice.find('input').prop('checked', true);
			}
			
		});
	}
});

awc.shipping.init = function($container) {
	// initialize form
	awc.shipping.$form = $container.find('.dti-form:first');
	awc.shipping.form = new awc.shipping.Form(awc.shipping.$form, awc.shipping.$form.find('#shipping-carriers'));
}

awc.shipping.get_selected_fields = function() {
	return awc.shipping.form.get_fields();
}


