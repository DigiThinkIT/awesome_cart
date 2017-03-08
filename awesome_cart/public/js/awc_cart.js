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
