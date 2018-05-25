/* global cart */
$(function() {

    function setupSlick() {
        // detect slick slider setups
        $(".slick-horizontal").each(function () {
            if ($(this).hasClass("slick-bounded")) {
                return;
            } else {
                $(this).addClass("slick-bounded");
                $(this).slick({
                    infinite: false,
                    slidesToShow: 4,
                    slidesToScroll: 4,
                    prevArrow: "<button type='button' class='slick-prev'><span class='glyphicon glyphicon-chevron-left'></span></button>",
                    nextArrow: "<button type='button' class='slick-next'><span class='glyphicon glyphicon-chevron-right'></span></button>",

                    responsive: [{
                        breakpoint: 1024,
                        settings: {
                            slidesToShow: 3,
                            slidesToScroll: 3,
                            infinite: false
                        }
                    }, {
                        breakpoint: 600,
                        settings: {
                            slidesToShow: 2,
                            slidesToScroll: 2,
                            dots: true,
                            infinite: false
                        }
                    }, {
                        breakpoint: 300,
                        settings: "unslick" // destroys slick
                    }]
                });
            }
        });
    }

    cart.on("tpl-ready", () => {
        setupSlick();
    });

    setupSlick();
});