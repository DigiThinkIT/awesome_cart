frappe.provide("frappe.integration_service")

frappe.integration_service.credit_gateway_gateway = Class.extend({
	init: function(addressForm, formData) {
		this.addressForm = addressForm;
		this.formData = formData;
		console.log("Credit gateway context", formData.context);
  },

	form: function() {
		this.$total_credit = $('#credit-gateway-form .credit-info .total-credit');
		this.$total_unpaid = $('#credit-gateway-form .credit-info .unpaid-balance');
		this.$order_total = $('#credit-gateway-form .credit-info .order-total');
		this.$available_credit = $('#credit-gateway-form .credit-info .available-credit');
		$('#credit-gateway-form .error').hide();
		this.validate();
	},

	process: function(overrides, callback) {
		var data = Object.assign({}, this.process_data, overrides);
		this._process(data, null, callback);
	},

  _process: function(data, request_name, callback) {
		awc.call("awesome_cart.awesome_cart.doctype.credit_gateway_settings.credit_gateway_settings.process",
			{
				options: data,
				request_name: request_name
			}, 1, "Processing Order. Please Wait..."
		)
		.then(function(resp) {
			var result = resp.data;
			if ( result.message.status == "Completed" ) {
				callback(null, result.message);
			} else {
				callback(result.message, null);
			}
		})
		.catch(function(err) {
			callback(err, null);
		});

  },

	collect_billing_info: function() {
    var billing_info = {};
    // collect billing field values

		var result = this.addressForm.validate();
		billing_info = $.extend({}, result.address);

    return billing_info;
  },

  collect: function() {
		this.total_credit = this.formData.context.total_credit;
		this.total_unpaid = this.formData.context.total_unpaid;
		var cart_totals = cart.totals;
		this.order_total = cart_totals.grand_total;
		this.available_credit = this.total_credit - this.total_unpaid;

		billing_info = this.collect_billing_info();

		this.process_data = {
			order_total: this.order_total,
			available_credit: this.available_credit,
      billing_info: billing_info,
    }
	},

	validate: function() {
    this.collect();
		var valid = true;
		var error = {};
		var address = {};

		/* disable momentarily until Eric figures out if JHA wants to enable
		 * checks on credit

		this.$total_credit.text('$'+this.total_credit.toFixed(2));
		this.$total_unpaid.text((this.total_unpaid>0?'-':'')+'$'+this.total_unpaid.toFixed(2));
		this.$order_total.text('$'+this.order_total.toFixed(2));
		this.$available_credit.text('$'+this.available_credit.toFixed(2));
		*/

		$('#credit-gateway-form .error').fadeOut('fast');

		/*
		if ( this.available_credit < this.order_total ) {
			$('#credit-gateway-form .feedback-not-enough-credit').fadeIn('fast');
			valid = false;
			error["credit"] = "Not Enough Credit Available";
		}*/

		if ( this.process_data.billing_info ) {
			if ( !this.process_data.billing_info.address_1 ) {
				valid = false;
				error['bill_line1'] = "Address line 1 is required";
			}

			if ( !this.process_data.billing_info.city ) {
				valid = false;
				error['bill_city'] = "City is required";
			}

			if ( !this.process_data.billing_info.pincode ) {
				valid = false;
				error['bill_pincode'] = "Postal Code is required";
			}

			if ( !this.process_data.billing_info.country ) {
				valid = false;
				error['bill_country'] = "Postal Code is required";
			}

			// copy address for awc
			for(var key in this.process_data.billing_info) {
				address[key] = this.process_data.billing_info[key]
			}
		} else {
			valid = false;
		}

		return {
      valid: valid,
      errors: error,
      address: address
   	};
	}

})
