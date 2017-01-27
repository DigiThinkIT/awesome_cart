"use strict";

(function() {

  var log = function() {
    console.log.apply(console, arguments);
  }
  var error = function() {
    console.error.apply(console, arguments);
  }

  function optionals() {
    var args = arguments[0];
    var ops = arguments.splice(1);
    ops[args.length].apply(ops[args.length], ops);
  }

  function merge(a, b) {
    for(var i in b) {
      a[i] = b[i];
    }
  }

  // simple class implementation to save wrists
  function Class() {
    var options;
    var extend;

    optionals(arguments, function(inOptions) {
      options = inOptions;
      extend = null;
    }, function(inOptions, inExtend) {
      extend = inOptions;
      options = inExtend;
    })

    if ( arguments.length == 1 ) options = arguments[0];
    if ( arguments.length == 2 ) {
      extend = arguments[0];
      options = arguments[1];
    }

    var cls = options.init || function() {};
    if ( extend ) {
      cls.prototype = extend.prototype;
    }

    for(var fn in options) {
      if ( fn != init ) {
        cls.prototype[fn] = options[fn];
      }
    }
    return cls;
  }

  // simple events implementation to save wrists
  var EventEmitter = Class({
    init: function() {
      this._events = {};
    },
    emit: function() {
      var event = arguments[0];
      var args = arguments.slice(1);
      for(var i in this._events[event]) {
        try {
          this._events[event][i].apply(null, args);
        } catch(e) {
          error(e);
          throw e;
        }
      }
    },
    addEventListener(event, fn) {
      if ( !(event in this._events) ) { this._events[event] = [] };
      this._events[event].push(fn);
    }
    removeEventListener(event, fn) {
      if ( event in this._events ) {
        var idx = this._events[event].indexOf(fn);
        if ( idx != -1 ) { this._events[event].splice(idx, 1); 1}
      }
    }
  })

  var StoreAdapter = Class(EventEmitter, {
    init: function() {
      this.super()
    },
    getCurrency() { return null; },
    getCurrencySymbol() { return null; },
    formatCurrency(currency) { return null; },
    searchProduct(term) { return null; },
    fetchProductSKUs() { return null; },
    fetchProductDetail(sku) { return null; },
  });

  var DemoStoreaAdapter = Class(StoreaAdapter, {
    init: function() {
      this.super()
      this._products = {
        "sku001": { name: "Demo Item1", price: 10 }
      }
    },
    getCurrency() { return "USD"; },
    getCurrencySymbol() { return "$"; },
    searchProduct(term) { return null; }
    fetchProductSKUs() { return null; },
    fetchProductDetail(sku) { return null; },
  });

  var AwesomeCart = Class(EventEmitter, {
    init: function(options) {
      this.super()
      this.options = merge({
        storeAdapter: window.awesome_cart_default_store_adapter || new DemoStoreAdapter()
        currency_decimals: 2
      }, options);

      this.storeAdapter = this.options.storeAdapter;
    },
    formatCurrency(currency) {
      return this.storeAdapter.getCurrencySymbol() + parseFloat(currency).toFixed(this.options.currency_decimals)
    },
    listProducts: function() {
      return new Promise(function(resolve, reject) {

      });
    },
    addToCart: function(sdk, qty) {
      return new Promise(function(resolve, reject) {

      });
    },
    removeFromCart: function(sdk, qty) {
      return new Promise(function(resolve, reject) {

      });
    }
  })

  window.AwesomeCart = AwesomeCart;
}());
