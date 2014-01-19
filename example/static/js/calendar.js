//$('#dashboard-picker').datepicker("option", "selectDate", true );
//
var forceUpdateDatePicker = function() {
    collapseToCurrentWeek($('#dashboard-picker'))
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
}

Backbone.history.bind("all", forceUpdateDatePicker)
forceUpdateDatePicker()
