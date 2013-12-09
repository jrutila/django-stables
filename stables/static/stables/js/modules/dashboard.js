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
    comparator: 'date',
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
        this.eventViews = {}
        this.$header = $('<div></div>')
    },
    tagName: 'div',
    render: function() {
        this.$header.html(this.model.get('date'))

        var that = this
        this.model.get('events').each(function(ev) {
            var hour = ev.getHour()
            if (!(ev.id in that.eventViews))
            {
                var evView = new EventView({ model: ev })
                that.$timeslots[hour].append(evView.$el)
            }
            evView.render()
        })
        for (var h in that.$timeslots)
            that.$timeslots[h].addClass('loaded')
        $('.timetable tbody tr:has(td.loaded:has(div))').show()
        $('.timetable tbody tr:not(:has(td.loaded:has(div)))').hide()
        return this
    },
})

function getHour(date) {
    return parseInt(date.split("T")[1].split(":")[0])
}

var WeekView = Backbone.View.extend({
    tagName: "table",
    className: "timetable",
    initialize: function() {
        this.model.on('change:days', this.render, this)
        this.$timeslots = {}
        this.dayViews = {}
    },
    template: _.template($('#WeekView').html()),
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        var $thead = $('<tr><th></th></tr>')
        var that = this
        var $tbody = this.$el.find('tbody')
        var hours = [8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        var daycount = 0
        this.model.get('days').each(function(day) {
            var $header = $("<th>"+day.get('date')+"</th>").appendTo($thead)
            daycount++
            if (!(day.get('date') in that.$timeslots)) {
                var $timeslot = {}
                _.each(hours, function(h) {
                    $timeslot[h] = $('<td></td>').append($('#EventLoadingView').html())
                })
                that.$timeslots[day.get('date')] = $timeslot
                var dayv = new DayView({ model: day })
                dayv.$timeslots = $timeslot
                that.dayViews[day.get('date')] = dayv
            }
        })
        this.$el.find('thead').append($thead)
        _.each(hours, function(h) {
            var $row = $('<tr><td>'+h+'</td></tr>').appendTo($tbody)
            that.model.get('days').each(function(day) {
                $row.append(that.$timeslots[day.get('date')][h])
            })
        })
        return this
    },
})
