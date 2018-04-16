class HorizontalGallery {
    constructor($el, config) {
        this.$el = $el;
        this.config = config;
        this.$container = $el.find(config.container);
        this.$leftControl = $el.find(config.leftControl);
        this.$rightControl = $el.find(config.rightControl);

        this.$leftControl.click(_ => {
            this.scrollLeft();
        });

        this.$rightControl.click(_ => {
            this.scrollRight();
        });
    }

    animateScrollEffect($container, $item, action, speed, skipShrink) {
        $container.css({ height: $container.height(), overflow: 'hidden' });
        let width = $item.width();
        $item.css({ overflow: 'hidden' })
        $item.animate({ width: 0 }, skipShrink?1:speed, function() {
            action($container, $item);
            $item.animate({ width: width }, speed, function () {
                $item.css({ width: '', overflow: '' });
                $container.css({ height: '', overflow: '' });
            });
        })

    }

    scrollLeft() {
        let $last = this.$container.children().last();
        this.animateScrollEffect(this.$container, $last, function($container, $item) {
            $container.prepend($item);
        }, 200, true);

    }

    scrollRight() {
        let $first = this.$container.children().first();
        this.animateScrollEffect(this.$container, $first, function($container, $item) {
            $container.append($first);
        }, 200);

    }
}

$.fn.horizontalGallery = function(config) {

    if ( $(this).data('_horizontal_gallery') ) {
        return $(this)
    }
    
    var _config = Object.assign({
        leftControl: ".control.left",
        rightControl: ".control.right",
        container: "ul"
    }, config || {})

    return $(this).each(function() {
        $(this).data('_horizontal_gallery', new HorizontalGallery($(this), _config));
    })
};


$(function () {
    cart.on('tpl-ready', () => {
        $('[data-horizontal-gallery]').horizontalGallery()
    })
});


