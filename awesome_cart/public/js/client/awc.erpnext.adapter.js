awc.ErpnextAdapter = function() {
  awc.StoreAdapter.prototype.constructor.call(this)
  this._templates = {}
}

awc.ErpnextAdapter.prototype = Object.create(awc.StoreAdapter.prototype)
/* TODO: fetch actual default currency from ERPNEXT */
awc.ErpnextAdapter.prototype.getCurrency = function() { return "USD"; }
/* TODO: fetch actual currecy symbol from ERPNext */
awc.ErpnextAdapter.prototype.getCurrencySymbol = function() { return "$"; }
/* TODO: fetch currecy formatting from ERPNext */
awc.ErpnextAdapter.prototype.formatCurrency = function(currency, decimals) { return `$${currency.toFixed(decimals)}`; }

awc.ErpnextAdapter.prototype.init = function() {
  var base = this;
  this.itemCache = {};
  return new awc.Promise(function(resolve, reject) {
    resolve(base.fetchCartSession())
  })
}

awc.ErpnextAdapter.prototype.loadTemplate = function(name) {
  // simple template caching.  Always cache the promise
  if ( this._templates[name] === undefined ) {
    return this._templates[name] = awc.get('/awc_template/' + name).then(function(resp) {
      return resp.body
    });
  } else {
    return this._templates[name]
  }
}

awc.ErpnextAdapter.prototype.fetchCartSession = function() {
  var base = this;
  return awc.get('/api/method/awesome_cart.awc.cart')
    .then(function(resp, xhr) {
      var data = JSON.parse(resp.body).message;
      if ( data.data.totals ) {
        base._totals = data.data.totals;
      }
      return data;
    })
}

awc.ErpnextAdapter.prototype.sessionAction = function(action, data) {
  var base = this;
  return new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.cart",
      args: {
        action: action,
        data: data
      },
      callback: function(result) {
        if ( result.message.success ) {
          if ( result.message.totals ) {
            base._totals = result.message.totals;
          }

          resolve(result.message.data)
        } else {
          reject(result.message.data)
        }
      }
    })
  })

}

awc.ErpnextAdapter.prototype.getProductBySKU = function(sku, detailed) {
  var base = this;
  if ( base.itemCache[sku] !== undefined ) {
    // return promise if curretly fetching
    if ( base.itemCache[sku].constructor == awc.Promise ) {
      return base.itemCache[sku];
    } else if (base.itemCache[sku].detailed == detailed) {
      // else return promise with cache data
      return new awc.Promise(function(resolve) {
        resolve(base.itemCache[sku]);
      })
    }
  }

  // otherwise, fetch item from backend
  return base.itemCache[sku] = new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.get_product_by_sku",
      args: { sku: sku, detailed: detailed?1:0 },
      callback: function(result) {
        if ( result.message.success ) {
          // only cache detailed items
          if ( detailed ) {
            base.itemCache[sku] = { data: message.data, detailed: detailed };
          }

          resolve(result.message.data)
        } else {
          reject(result.message)
        }
      }
    })
  })

}

awc.ErpnextAdapter.prototype.fetchProducts = function(tags, terms, start, limit) {
  if ( !tags ) tags = []
  var base = this;
  return new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.fetch_products",
      args: { tags: tags.join(','), terms: terms, start: start?start:0, limit: limit?limit:9 },
      callback: function(result) {
        if ( result.message.success ) {
          if ( result.message.data.totals ) {
            base._totals = result.message.data.totals;
          }

          resolve(result.message.data)
        } else {
          reject(result.message.data)
        }
      }
    })
  })
}

awc.ErpnextAdapter.prototype.validate = function(gateway_request) {
  /* We expect this method to be called when awc's gateway provider's submit
     button is clicked.

     We'll use this call to feed payment request information to the gateway
     before it can be submitted */

     console.log(arguments);

    if ( !gateway_request ) {
      throw "gateway_request is not set";
    }

    frappe.call({
      method: "awesome_cart.awc.create_transaction",
      freeze: true,
      callback: function(data) {
        var result = data.message;
        if ( result.success ) {
          // copy validation data to continue checkout process
          for(var k in result.data ) {
            gateway_request[k] = result.data[k];
          }

          console.log("Preparing for checkout!", gateway_request);

          gateway_provider.process(gateway_request, function(err, data) {
            if ( err ) {
              console.error(err);
            } else {
              window.location.href = data.redirect_to;
            }
          });
        } else {
          console.error(data);
        }
      }
    })
}

// Initialize awc cart
var cart = new awc.AwesomeCart({
  storeAdapter: new awc.ErpnextAdapter()
});

awc.debug.level = 5;

$(function() { cart.bootstrap() });
