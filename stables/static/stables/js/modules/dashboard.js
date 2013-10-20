var Day = Backbone.Model.extend({
    url: function() {
        return apiUrl+'events/?at='+this.get('date')
    },
    parse: function(data) {
        data['events'] = new EventCollection(EventCollection.prototype.parse(data.objects))
        delete data.objects
        return data
    },
    defaults: {
        events: new EventCollection(),
    },
    getEventsInHour: function(hour) {
        return this.get('events').filter(function(ev) {
            return ev.getHour() == hour
        })
    },
})

var DayCollection = Backbone.Collection.extend({
    model: Day,
})

var Week = Backbone.Model.extend({
    initialize: function(data) {
        this.set('dates', _.object(data.dates, []))
    },
    defaults: {
        days: new DayCollection(),
    },
    fetch: function() {
        var that = this
        console.log('fetch')
        var newColl = new DayCollection()
        _.each(this.get('dates'), function(day, key) {
            if (day == undefined)
            {
                day = new Day()
                day.set('date', key)
                day.fetch()
            }
            newColl.add(day)
            that.get('dates')[key] = day
        })
        that.set('days', newColl)
    },
})

var DayView = Backbone.View.extend({
    initialize: function() {
        this.listenTo(this.model, "change", this.render)
        this.$timeslots = {}
        this.$header = $('<div></div>')
    },
    tagName: 'div',
    render: function() {
        this.$header.html(this.model.get('date'))

        var that = this
        this.model.get('events').each(function(ev) {
            var hour = ev.getHour()
            if (!(hour in that.$timeslots))
                that.$timeslots[hour] = []
            var evView = new EventView({model: ev})
            that.$timeslots[hour].push(evView)
            evView.render()
        })
        this.trigger("timeslots", this)

        return this
    },
})

function addAndGet($tr, nth, finalLength) {
    var len = $tr.find("td").length
    console.log(len, nth, finalLength)
    if (len > nth)
        return $tr.find('td').eq(nth)

    var $ret = undefined
    for (var i = len; i <= finalLength; i++)
    {
        var $r = $("<td></td>").appendTo($tr)
        if (i == nth)
            $ret = $r
    }
        
    return $ret
}

var WeekView = Backbone.View.extend({
    tagName: "table",
    initialize: function() {
        this.model.on('change:days', this.render, this)
        this.dayViews = {}
        this.$timeslots = {}
    },
    template: _.template($('#WeekView').html()),
    render: function() {
        console.log('week render')
        this.$el.html(this.template(this.model.attributes))
        var $thead = $('<tr><th></th></tr>')
        var that = this
        this.model.get('days').each(function(day) {
            var $header = $("<th></th>").appendTo($thead)
            if (!(day.get('date') in that.dayViews))
            {
                var dayv = new DayView({ model: day })
                that.dayViews[day.get('date')] = dayv
                that.listenTo(dayv, "timeslots", that.renderTimes)
            } else {
                var dayv = that.dayViews[day.get('date')]
                dayv.trigger("timeslots", dayv)
            }
            $header.html(that.dayViews[day.get('date')].$header)
        })
        this.$el.find('thead').append($thead)
        return this
    },
    renderTimes: function(dayView) {
        $(this).find('.loading').remove()
        var that = this
        var $body = this.$el.find('tbody')
        var dayPos = this.model.get('days').indexOf(dayView.model)+1
        console.log("dayPos: "+dayView.model.get('date')+":"+dayPos)
        _.each(_.pairs(dayView.$timeslots), function(p) {
            var hour = parseInt(p[0])
            if (!(hour in that.$timeslots))
                that.$timeslots[hour] = $('<tr><td>'+hour+'</td></tr>')
            var $hour = that.$timeslots[hour]
            var hours = _.keys(that.$timeslots).sort(function (a,b) { return parseInt(a)-parseInt(b); })
            var pos = hours.indexOf(hour.toString())
            if (pos == 0)
                $body.prepend($hour)
            else
            {
                var $prev = $body.find("tr").eq(pos)
                if ($prev.length == 0)
                    $body.append($hour)
                else
                    $prev.before($hour)
            }
            var $td = addAndGet($hour, dayPos, _.values(that.dayViews).length)
            $td.html("")
            _.each(p[1], function(ev) {
                $td.append(ev.$el)
            })
        })

    },
})
