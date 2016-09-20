frappe.provide("awc");

awc.PagesPanel = Class.extend({
	init: function($panel, default_panel) {
		var scope = this;
		this.$panel = $panel;

		this.$panel.data("awc_pagespanel", this);
		this.$panel.children().addClass('aw-pagepanel-page').hide();
		this.$panel.find('[data-aw-goto]').click(function() {
			var selector = $(this).attr('data-aw-goto');
			if ( selector == '!next' ) {
				scope.next();
			} else {
				scope.show(selector);
			}
		});

		this.show(default_panel);
	},

	show: function(selector) {
		if ( $(selector).length == 0 ) {
			console.error("Page not found: ", selector);
			return false;
		} else {
			this.$panel.find('aw-pagespanel-page.active').slideUp('fast').removeClass('active');
			$(selector).slideDown('fast').addClass('active');
			return true;
		}
	},

	next: function($page) {
		if ( !$page ) {
			$page = this.$panel.find('.aw-pagepanel-page.active');
		}
		var next_selector = $active.attr('data-next');

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

