var DayLimit = Backbone.Model.extend({
    defaults: {
        'amount': 0
    },
    increase: function() {
        this.set('amount', this.get('amount') + 1);
        var over = this.get('limit') - this.get('amount')
        if (over == -1)
            this.trigger('topped', this)
    },
    decrease: function() {
        this.set('amount', this.get('amount') - 1);
        var over = this.get('limit') - this.get('amount')
        if (over == 0)
            this.trigger('cleared', this)
    },
    isTopped: function() {
        var over = this.get('limit') - this.get('amount')
        return over <= -1
    },
})

var DayLimits = Backbone.Collection.extend({
    model: DayLimit,
    increase: function(horse) {
        if (horse)
            this.findLimit(horse).increase()
    },
    decrease: function(horse) {
        if (horse)
            this.findLimit(horse).decrease()
    },
    findLimit: function(horse) {
        return this.find(function(h) { return h.get('horse') == horse; })
    },
})

var Day = Backbone.Model.extend({
    initialize: function() {
        this.set('limits', new DayLimits(horseLimits.toJSON()))
    },
    url: function() {
        return apiUrl+'events/?at='+this.get('date')
    },
    parse: function(data) {
        data['events'] = new EventCollection(EventCollection.prototype.parse(data.objects), { 'limits': this.get('limits')})
        delete data.objects
        return data
    },
    defaults: {
        events: new EventCollection(),
        limits: new DayLimits(),
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
        this.listenTo(this.model.get('limits'), "topped", this.limitTopped)
        this.$timeslots = {}
        this.eventViews = {}
        this.$header = $('<div></div>')
    },
    limitTopped: function(limit) {
        var content = $('<div></div>')
        content.append(_.template($('#HorseLimitReachedMessage').html(), limit.attributes))
        $.msgGrowl({
            type: 'warning',
            title: content.find('h4').html(),
            text: content.find('span').html(),
        })
    },
    tagName: 'div',
    render: function() {
        this.$header.html(this.model.get('date'))
        this.$header.append("&nbsp;<a href='/p/daily/"+this.model.get('date')+"/'><i class='icon-print'></i></a>")

        var that = this
        for (var h in that.$timeslots)
            that.$timeslots[h].html($('#EventLoadingView').html())
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
        var hours = [4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        var daycount = 0
        this.model.get('days').each(function(day) {
            var $header = $("<th>"+day.get('date')+"</th>").appendTo($thead)
            $header.append("&nbsp;<a href='/p/daily/"+day.get('date')+"/'><i class='icon-print'></i></a>")
            daycount++
            if (!(day.get('date') in that.$timeslots)) {
                var $timeslot = {}
                _.each(hours, function(h) {
                    $timeslot[h] = $('<td></td>').append($('#EventLoadingView').html())
                })
                that.$timeslots[day.get('date')] = $timeslot
                var dayv = new DayView({ model: day })
                dayv.$timeslots = $timeslot
                dayv.$header = $header
                that.dayViews[day.get('date')] = dayv
            } else {
                that.dayViews[day.get('date')].render()
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
