var collapseToCurrentWeek = function(that) {
    window.setTimeout(function () {
        $(that).find("tbody tr:not(:has(td.ui-state-highlight))").hide()
        $(that).addClass('collapsed')
    }, 1);
}

var forceUpdateDatePicker = function() {
    if (typeof dashboard_router != 'undefined')
    {
        var dates = []
        var fragment = Backbone.history.fragment
        if (fragment == "")
        {
            dates.push(new Date())
        } else {
            frgs = fragment.split(',')
            for (var d in frgs)
            {
                dates.push(new Date(frgs[d]))
            }
        }

        $('#dashboard-picker').multiDatesPicker("resetDates");
        $('#dashboard-picker').multiDatesPicker("addDates", dates );
    }
    collapseToCurrentWeek($('#dashboard-picker'))
}

$(document).ready(function() {
    Backbone.history.bind("all", forceUpdateDatePicker)
    forceUpdateDatePicker()

    $(document).ready(function() {
        $(".wide").parent(".container").removeClass('container').addClass('dashboard-container')
        $(".ui-datepicker-year").after("<b class='caret'></b>")
    });


    $('#dashboard-picker').multiDatesPicker({
        showOtherMonths: true,
        firstDay: 1,
        selectOtherMonths: true,
        maxPicks: 7,
        showWeek: true,
        onSelect: function(dateText, inst) {
            var dates = inst.dpDiv.parent().multiDatesPicker('getDates', 'object')
            if ($('body').hasClass('mobile'))
            {
                inst.dpDiv.parent().multiDatesPicker('resetDates')
                inst.dpDiv.parent().multiDatesPicker('addDates', [dateText])
                dates = inst.dpDiv.parent().multiDatesPicker('getDates', 'object')
            }
            fragment = _.chain(dates).map(function (dd) { return $.datepicker.formatDate('yy-mm-dd', dd); }).join(',').value()
            if (typeof dashboard_router != 'undefined')
                dashboard_router.navigate(fragment, {trigger:true});
            else
                window.location=dashboardUrl+"#"+fragment
            collapseToCurrentWeek($('#dashboard-picker'))
        }
    });

    $("#dashboard-picker").datepicker($.datepicker.regional[ "fi" ] );
    $(".weekdate-picker .ui-datepicker-title").on("click", function() {
        $picker = $(this).parents(".weekdate-picker")
        if ($picker.hasClass('collapsed')) {
            $picker.find("tbody tr").show()
            $picker.removeClass('collapsed')
        } else {
            collapseToCurrentWeek($picker)
        }
    });

    $('.weekdate-picker .ui-datepicker-calendar tr').on('mousemove', function() { $(this).find('td a').addClass('ui-state-hover'); });
    $('.weekdate-picker .ui-datepicker-calendar tr').on('mouseleave', function() { $(this).find('td a').removeClass('ui-state-hover'); });

    /*
    $('.mainnav li:eq(0)').live('mousemove', function() {
        $(this).parents(".subnavbar-inner").next(".subnavbar-inner").removeClass("collapse");
    });
    $('.subnavbar:has(li:eq(0):not(.active))').on('mouseleave', function() {
        $(this).find(".subnavbar-inner:eq(1)").addClass("collapse");
    });
    */
});

