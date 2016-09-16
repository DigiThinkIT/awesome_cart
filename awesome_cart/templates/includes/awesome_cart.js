frappe.provide("awc.ui");

awc.ui.goto = function(selector) {
	if ( $(selector).length == 0 ) {
		console.error("!aw page selector does not exist:", selector);
	}

	$('.checkout-page.active').slideUp('fast').removeClass('active');
	$(selector).slideDown('fast').addClass('active');
}


$('.checkout-page').hide();
$('[data-aw-goto]').click(function() {
	if ( !$(this).closest('.dti-form').hasClass('incomplete') ) {
		var selector = $(this).attr('data-aw-goto');
		awc.ui.goto(selector);
	}
});
