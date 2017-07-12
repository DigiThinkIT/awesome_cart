frappe.provide("frappe.gateway_selector")

frappe.gateway_selector.credit_gateway_embed = frappe.integration_service.credit_gateway_gateway.extend({
  _initialized: false,
	/**
   * Called when the form is displayed
   */
  show: function() {
    if ( !this._initialized ) {
      this.form('');
    }

    $('#gateway-selector-continue').text("Bill Me Later");
  },

  /**
   * Called when the form is hidden
   */
  hide: function() {
    // form was hidden
  },

	getSummary: function() {
		this.collect()

		return frappe.render(frappe.templates.credit_gateway_summary, Object.assign({
      }, this.process_data));
	}
});
