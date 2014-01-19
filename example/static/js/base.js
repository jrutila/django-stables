var collapseToCurrentWeek = function(that) {
    window.setTimeout(function () {
        $(that).find("tbody tr:not(:has(td.ui-state-highlight))").hide()
        var is_caret = $(that).find(".ui-datepicker-title .caret").show()
        if (is_caret.length == 0)
            $(that).find(".ui-datepicker-year").after("<b class='caret'></b>")
    }, 1);
}

$(function () {
    $('.lightbox-type').lightbox ()

    $(document).on("submit", '.jquery-lightbox-html form', null, function(ev) {
        var $form = $(ev.currentTarget)
        $.post($form.attr("action"), $form.serialize(), function(data){
            $form.parent().html(data)
        })
        return false
    })

    $(document).ready(function() {
        $(".wide").parent(".container").removeClass('container').addClass('dashboard-container')
    })


    $('#dashboard-picker').multiDatesPicker({
        showOtherMonths: true,
        firstDay: 1,
        selectOtherMonths: true,
        maxPicks: 7,
        showWeek: true,
        onSelect: function(dateText, inst) {
            var dates = inst.dpDiv.parent().multiDatesPicker('getDates', 'object')
            fragment = _.chain(dates).map(function (dd) { return $.datepicker.formatDate('yy-mm-dd', dd); }).join(',').value()
            console.log(fragment)
            if (typeof dashboard_router != 'undefined')
                dashboard_router.navigate(fragment, {trigger:true});
            else
                window.location=dashboardUrl+"#"+fragment
            collapseToCurrentWeek($('#dashboard-picker'))
        },
    })

    $("#dashboard-picker").datepicker($.datepicker.regional[ "fi" ] );
    $(".weekdate-picker .ui-datepicker-title").live("click", function() {
        $(this).parents(".ui-datepicker").find("tbody tr").show()
        $(this).find(".caret").hide()
    })

    $('.weekdate-picker .ui-datepicker-calendar tr').live('mousemove', function() { $(this).find('td a').addClass('ui-state-hover'); });
    $('.weekdate-picker .ui-datepicker-calendar tr').live('mouseleave', function() { $(this).find('td a').removeClass('ui-state-hover'); });

    $('.mainnav li:eq(0)').live('mousemove', function() {
        $(this).parents(".subnavbar-inner").next(".subnavbar-inner").removeClass("collapse");
    });
    $('.subnavbar:has(li:eq(0):not(.active))').on('mouseleave', function() {
        $(this).find(".subnavbar-inner:eq(1)").addClass("collapse");
    });
});

