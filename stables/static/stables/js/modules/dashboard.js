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

var Horse = Backbone.Model.extend({})

var HorseCollection = Backbone.Collection.extend({
    model: Horse,
    initialize: function(models, options) {
        this.date = options.date;
    },
    url: function() {
        return apiUrl+'horse/?last_usage_date__gte='+this.date+'&limit=0';
    }
})

var Day = Backbone.Model.extend({
    initialize: function(opts) {
        this.set('limits', new DayLimits(horseLimits.toJSON()));
        this.set('horses', new HorseCollection([], opts));
        this.get('horses').fetch({async: false});
    },
    url: function() {
        return apiUrl+'events/?at='+this.get('date')
    },
    parse: function(data) {
        data['events'] = new EventCollection(EventCollection.prototype.parse(data.objects), {
            'limits': this.get('limits'),
            'horses': this.get('horses')
        });
        data['events'].each(function(ev) {
            this.listenTo(ev, "action:move", function(a,b) {
                console.log("Fetching because action:move")
                if (!moment(this.get("date")).isSame(moment(b.start), "day"))
                {
                    console.log("Event moved out of day "+this.get("date"))
                    this.trigger("eventout", a);
                }
                this.fetch();
                console.log("Fetch ready after action:move")
            });
        },this);
        delete data.objects
        return data
    },
    defaults: {
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
    comparator: 'date'
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
                day = new Day({'date': key})
                day.fetch()
                day.on("eventout", function(movedEvent) {
                    var kk = moment(movedEvent.get("start")).format("YYYY-MM-DD");
                    var dd = that.get("dates")[kk];
                    dd && dd.fetch();
                });
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
        content.append(_.template($('#HorseLimitReachedMessage').html())(limit.attributes))
        $.msgGrowl({
            type: 'warning',
            title: content.find('h4').html(),
            text: content.find('span').html(),
        })
    },
    tagName: 'div',
    render: function() {
        var that = this
        for (var h in that.$timeslots)
        {
            that.$timeslots[h].html($('#EventLoadingView').html())
            that.$timeslots[h].addClass('unloaded')
        }
        this.model.get('events').each(function(ev) {
            var hour = ev.getHour()
            if (!(ev.id in that.eventViews))
            {
                var evView = new EventView({ model: ev })
                that.$timeslots[hour].append(evView.$el)
                evView.on("courseChanged", function(course) {
                    that.trigger("courseChanged", course);
                });
            }
            evView.render()
        })
        for (var h in that.$timeslots)
            that.$timeslots[h].addClass('loaded').removeClass('unloaded')
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
    createDayViews: function() {

    },
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        var headerTmpl = _.template($("#DayHeaderView").html());
        var $thead = $('<tr><th class="ui-time"></th></tr>')
        var that = this
        var $tbody = this.$el.find('tbody')
        var hours = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        this.model.get('days').each(function(day) {
            var $header = $("<th></th>").appendTo($thead);
            $header.append(headerTmpl({
                date: moment(day.get('date')).format('l'),
                print_url: '/p/daily/'+day.get('date')
            }));
            var ae = new AddEventButtonView({
                model: new Backbone.Model({ date: day.get('date') }),
                el: $header.find(".add-course")
            });
            ae.render();
            ae.on("eventAdded", function(start) {
                var date = moment(start).format("YYYY-MM-DD");
                if (_.has(that.dayViews, date))
                    that.dayViews[date].model.fetch();
                else
                    console.log("No date "+date+" visible");
            });
            $header.append(ae.$el)
            if (!(day.get('date') in that.$timeslots)) {
                var $timeslot = {}
                _.each(hours, function(h) {
                    $timeslot[h] = $('<td class="unloaded"></td>').append($('#EventLoadingView').html())
                })
                that.$timeslots[day.get('date')] = $timeslot
                var dayv = new DayView({ model: day })
                dayv.$timeslots = $timeslot
                dayv.$header = $header
                dayv.on("courseChanged", function(course) {
                    _.each(that.dayViews, function(dv) {
                        dv.model.fetch();
                    });
                });
                that.dayViews[day.get('date')] = dayv
                if (dayv.model.has('events'))
                    dayv.render()
            } else {
                that.dayViews[day.get('date')].render()
            }
        });
        this.$el.find('thead').append($thead)
        _.each(hours, function(h) {
            var $row = $('<tr><td class="ui-time">'+h+'</td></tr>').appendTo($tbody)
            that.model.get('days').each(function(day) {
                $row.append(that.$timeslots[day.get('date')][h])
            })
            if (!$row.is(':has(td.unloaded)') && $row.is(':not(:has(td.loaded:has(div)))'))
                $row.hide()
        })
        return this
    },
})
