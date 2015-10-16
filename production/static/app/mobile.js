/**
 * Created by jorutila on 16.9.2015.
 */
var checkMobile = function() {
    if ($(window).width() <= 798)
    {
        jQuery('body').addClass('mobile');
    } else {
        jQuery('body').removeClass('mobile');
    }
}

$(window).resize(checkMobile)
$(document).ready(checkMobile)
