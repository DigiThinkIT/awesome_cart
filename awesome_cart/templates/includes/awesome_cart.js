
function aw_goto(selector) {
	if ( $(selector).length == 0 ) {
		console.error("!aw page selector does not exist:", selector);
	}

	$('.checkout-page.active').slideUp('fast').removeClass('active');
	$(selector).slideDown('fast').addClass('active');
}

$('.checkout-page').hide();
$('[data-aw-goto]').click(function() {
	var selector = $(this).attr('data-aw-goto');
	aw_goto(selector);
});
