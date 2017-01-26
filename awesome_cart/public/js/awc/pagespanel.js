frappe.provide("awc");

awc.PagesPanel = Class.extend({
	init: function($panel, default_panel) {
		var scope = this;

		this._default_panel = default_panel;
		this._on_show_handlers = {};
		this._on_hide_handlers = {};
		this.$panel = $panel;

		this.$panel.data("awc_pagespanel", this);
		this.$panel.children().addClass('awc-pagespanel-page').hide();
		this.$panel.find('[data-aw-goto]').click(function() {
			var $form = $(this).closest('.dti-form');

			if ( $form.length > 0 && $form.hasClass("incomplete") && $(this).hasClass('btn-primary') ) {
				return; // ignore click on incomplete dti forms for primary buttons
			}

			var selector = $(this).attr('data-aw-goto');
			if ( selector == '!next' ) {
				scope.next();
			} else if ( selector == '!back' ) {
				scope.back();
			} else {
				scope.show(selector);
			}
		});

	},
	
	start: function() {
		this.show(this._default_panel);
	},

	on_show: function(page_selector, fn) {
		var parts = page_selector.split(' ');

		$.each(parts, (function(i, page_selector) {
			if ( !(page_selector in this._on_show_handlers) ) {
				this._on_show_handlers[page_selector] = [];
			}

			this._on_show_handlers[page_selector].push(fn);
		}).bind(this));
	},

	on_hide: function(page_selector, fn) {

		var parts = page_selector.split(' ');

		$.each(parts, (function(i, page_selector) {
			if ( !(page_selector in this._on_hide_handlers) ) {
				this._on_hide_handlers[page_selector] = [];
			}

			this._on_hide_handlers[page_selector].push(fn);
		}).bind(this));
	},

	show: function(selector) {
		if ( $(selector).length == 0 ) {
			console.error("Page not found: ", selector);
			return false;
		} else {
			var $active = this.$panel.find('.awc-pagespanel-page.active');
			if ( $active.length > 0 ) {
				$(selector).attr('data-back-ref', '#' + $active.attr('id'));

				var active_selector = '#' + $active.attr('id');
				if ( active_selector in this._on_hide_handlers) {
					for( var i in this._on_hide_handlers[active_selector]) {
						var fn = this._on_hide_handlers[active_selector][i];
						if ( typeof fn == 'function' ) {
							fn();
						}
					}
				}
			}

			$active.slideUp('fast').removeClass('active');
			$(selector).slideDown('fast').addClass('active');
			if ( selector in this._on_show_handlers) {
				for( var i in this._on_show_handlers[selector]) {
					var fn = this._on_show_handlers[selector][i];
					if ( typeof fn == 'function' ) {
						fn();
					}
				}
			}

			return true;
		}
	},

	back: function() {
		$page = this.$panel.find('.awc-pagespanel-page.active');
		var back_ref = $page.attr('data-back-ref');
		$page.removeAttr('data-back-ref');
		this.show(back_ref);
	},

	next: function($page) {
		if ( !$page ) {
			$page = this.$panel.find('.awc-pagespanel-page.active');
		}
		var next_selector = $page.attr('data-next');

		if ( next_selector ) {
			$next = $(next_selector);
			if ( $next.is('.disabled') ) {
				return this.next($next);
			} else {
				return this.show(next_selector);
			}
		}

		return false;
	}

});

awc.page_panel = null;

