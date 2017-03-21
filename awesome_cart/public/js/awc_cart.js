window.awc_checkout = {};

awc_checkout = {
  showPage: function(page) {
    $('.panel').slideUp('fast');
    $(page).slideDown('fast');
    var bcSelector = $(page).attr('data-bc');
    if ( bcSelector ) {
      var $bc = $(bcSelector);
      $('#checkout-breadcrumb .breadcrumb')
        .not($bc)
        .removeClass('active');
      $bc.addClass('active');
    }

    // run through validations as necessary to update summaries
    // TODO: Add shipping validation
    var checkout_enabled = true;
    if ( awc_checkout.gateway_provider ) {
      var billing_summary = awc_checkout.gateway_provider.getSummary();
      $('#checkout-confirm-billing .content').empty().append(billing_summary);

      var billing_validation_response = awc_checkout.gateway_provider.validate();
      console.log(billing_validation_response);

      if ( billing_validation_response.valid == false) {
        console.log("Disable checkout")
        checkout_enabled = false
      }

      awc_checkout.billing_address = billing_validation_response.address
      //TODO: replace shipping address with actual data
      awc_checkout.shipping_address = {}
      for(key in awc_checkout.billing_address) {
        var k = key.replace("billing_", "shipping_")
        awc_checkout.shipping_address[k] = awc_checkout.billing_address[key]
      }


      awc_checkout.gateway_provider.enable(checkout_enabled);
    }

  },

  nextPage: function() {
    var $page = $('.panel:visible');
    awc_checkout.showPage($page.next());
  },

  setupPage: function() {
    $('.panel .btn-next').click(awc_checkout.nextPage);

    $('#checkout-confirm-shipping .btn-primary').click(function() {
      awc_checkout.showPage('#checkout-shipping');
    })

    $('#checkout-confirm-billing .btn-primary').click(function() {
      awc_checkout.showPage('#checkout-billing');
    })

    $('#bc-shipping').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-shipping'); });
    $('#bc-billing').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-billing'); });
    $('#bc-checkout').click(function(e) { e.preventDefault(); awc_checkout.showPage('#checkout-confirmation'); });

    // create a full cart feed from awesom cart js
    cart.newCartFeed('cart-full', {
      container: '#cart-full',
      tpl: cart.template('cart-full')
    })

    function onCartChanges() {

      // FIX: Babelfish issue, cart.totalItems getter not invoked in IF statement
      var totalItems = cart.totalItems;
      // make sure panels are visible once cart is processed and has items
      if ( totalItems > 0 ) {
        $('#checkout-panels').fadeIn('fast')
      } else {
        $('#checkout-panels').hide()

      }
    }

    cart.on('init', onCartChanges);
    cart.on('update', onCartChanges);
  }
}

awc_checkout.setupPage();
