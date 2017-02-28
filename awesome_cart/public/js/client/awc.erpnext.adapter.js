awc.ErpnextAdapter = function() {
  this._templates = {}
}

awc.ErpnextAdapter.prototype = Object.create(awc.StoreAdapter)
awc.ErpnextAdapter.prototype.getCurrency = function() { return "USD"; }
awc.ErpnextAdapter.prototype.getCurrencySymbol = function() { return "$"; }
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
  return awc.get('/api/method/awesome_cart.awc.cart')
    .then(function(resp) {
      var data = JSON.parse(resp.body).message;
      return data;
    })
}

awc.ErpnextAdapter.prototype.sessionAction = function(action, data) {
  return awc.post({
      url: '/api/method/awesome_cart.awc.cart',
      body: JSON.stringify({action: action, data: data}),
      headers: {
        "X-Frappe-CSRF-Token": frappe.csrf_token,
        "Content-Type": "application/json"
      }
    })
    .then(function(resp) {
      var data = JSON.parse(resp.body).message
      return data;
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
  return new awc.Promise(function(resolve, reject) {
    frappe.call({
      method: "awesome_cart.awc.fetch_products",
      args: { tags: tags.join(','), terms: terms, start: start?start:0, limit: limit?limit:9 },
      callback: function(result) {
        if ( result.message.success ) {
          resolve(result.message.data)
        } else {
          reject(result.message.data)
        }
      }
    })
  })
}

// Initialize awc cart
var cart = new awc.AwesomeCart({
  storeAdapter: new awc.ErpnextAdapter()
});

awc.debug.level = 5;

$(function() { cart.bootstrap() });
