frappe.provide("awc.gateway");

awc.gateway.Form = awc.Form.extend({
	init: function($form) {
		this._super($form);

		var $gwform = this.$form;

		// ugly hack, move this to css
		$('.gateway', $gwform).hide();


		// makes sure gateway selector radio value is updated
		$gwform.find('#gateway-selectors .selected').each(function() {
			var ref = $(this).attr('data-ref');
			$(ref).show();
			$(this).find('input').prop("checked", true);
		});

		$gwform.find('.btn-action').on('submit_action', function() {
			$(window).trigger('gateway_pay_action');
		});
	}

});

awc.gateway.init = function($container) {
	// handles gateway selector click toggle
	
	awc.gateway.$container = $container;
	var $gateway_selectors = $container.find('#gateway-selectors .selector');
	awc.gateway.selectors = $gateway_selectors;
	
	// hide all non selected gateways
	$gateway_selectors.not('.selected').each(function() {
		var ref = $(this).attr('data-ref');
		$(ref).hide();
	});
	
	// make sure default selected radio button is set
	$gateway_selectors.filter('.selected').find('input').prop("checked", true);
	
	$gateway_selectors.click(function() {
		// handle toggle classes for other selectors
		$gateway_selectors.not($(this)).each(function() {
			$(this).removeClass('selected');
			var ref = $(this).attr('data-ref');
			$(ref).slideUp('fast');
			$(this).find('input').prop("checked", false);
		});
		
		var ref = $(this).attr('data-ref');
		$(ref).slideDown('fast');
		$(this).addClass('selected');
		$(this).find('input').prop("checked", true);
	});
	
	// initialize forms
	$container.find('.dti-form').each(function() {
		new awc.gateway.Form($(this));
	});
};

awc.gateway.get_selected_form = function() {
	var $gwform = awc.gateway.$container;
	var $selected = $gwform.find('#gateway-selectors .selected:first input:checked');
	return { $el: $selected, value: $selected.val() };
};

awc.gateway.update_fields = function($form) {
	awc.gateway.selectors.filter("[data-ref='#" + $form.attr("id") + "']").click();
	$form.data("awc_form").check_required();
};

awc.gateway.get_selected_fields = function() {
	var gateway = awc.gateway.get_selected_form();
	var $gateway_form = awc.gateway.$container.find("[data-gateway-id='"+gateway.value+"']");
	return $gateway_form.data("awc_form").get_fields();
};

