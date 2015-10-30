(function ($target) {

        function loadScript(url, callback) {
            var script = document.createElement("script")
            script.type = "text/javascript";
            if (script.readyState) { //IE
                script.onreadystatechange = function () {
                    if (script.readyState == "loaded" || script.readyState == "complete") {
                        script.onreadystatechange = null;
                        callback();
                    }
                };
            } else { //Others
                script.onload = function () {
                    callback();
                };
            }

            script.src = url;
            document.getElementsByTagName("head")[0].appendChild(script);
        }

        loadScript("http://code.jquery.com/jquery-1.10.1.min.js", function () {
$('head').append("<script src='http://code.jquery.com/jquery-migrate-1.2.1.min.js'></script>");
$('head').append("<script type='text/javascript' src='http://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.5.2/underscore-min.js'></script>");
        loadScript("http://cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/moment.min.js", function () {
$('head').append("<script type='text/javascript' src='http://cdnjs.cloudflare.com/ajax/libs/moment.js/2.5.1/lang/fi.js'></script>");

var eventTemplate = '<span style="font-weight: bold; <% if (cancelled) { %>text-decoration: line-through; color: red;<% } %>"><% if (typeof original_start !== "undefined") { %> <%= original_start.format("HH:mm") %> &#8658; <%= start.format("dd DoM HH:mm") %>-<%= end.format("HH:mm") %> <% } else { %> <%= start.format("dd DoM HH:mm") %>-<%= end.format("HH:mm") %> <% } %> <%= title %></span> <% if (!cancelled && typeof free_slots !== "undefined") { %><div><%= free_amount %> paikka<% if (free_amount > 1) { %>a<% } %> vapaana</div><% } else if (cancelled) { %>Peruttu!<% } %>';

var url = $target.attr('data-url');
var start = moment().format("YYYY-MM-DD");
var end = moment().add('days', $target.attr('data-days')).format("YYYY-MM-DD");

$.ajax(url+'api/timetable/?start='+start+'&end='+end)
.done(function(data) {
    var $output = $('<ul></ul>')
    var start = new Date(data['start']);
    var end = new Date(data['end']);
    for (var d = start; d <= end; d.setDate(d.getDate() + 1))
    {
        var md = moment(d);
        var events = data['dates'][md.format('YYYY-MM-DD')]
        _.each(_.sortBy(events, function(ev) { return ev['start']; })
            ,function(ev) {
                ev['start'] = moment(ev['start']);
                ev['end'] = moment(ev['end']);
                if ('original_start' in ev)
                    ev['original_start'] = moment(ev['original_start']);
                if ('original_end' in ev)
                    ev['original_end'] = moment(ev['original_end']);
                if (! 'cancelled' in ev)
                    ev['cancelled'] = False;
                var text = _.template(eventTemplate, ev);
                //$output.append($('<li>'+md.format('dd DoM')+'</li>'));
                if (ev['free_slots'])
                    $output.append($('<li>'+text+'</li>'));
            });
    }
    $target.html(
        $output
    );
});

        });
        });

})((typeof(target) != "undefined" && $(target)) || $('#stables-timetable'));
