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
        })
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
                day = new Day({'date': key})
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

var AddEventButtonView = Backbone.View.extend({
    tagName: 'a',
    className: 'addevent',
    events: {
        'click': 'addEvent',
    },
    render: function() {
        this.$el.html("<i class='fa fa-plus'></i>")
        this.$el.css('cursor', 'pointer');
    },
    addEvent: function(ev) {
        var v = new AddEventView({ 'model': this.model });
        v.render();
        var that = this;
        v.on('eventAdded', function() {
            that.trigger('eventAdded');
        });
    }
})

var AddEventView = Backbone.View.extend({
    events: {
        "submit": 'submitEvent'
    },
    render: function() {
        var html, $oldel=this.$el, $newel;
        html = _.template($('#AddEventView').html(), this.model.attributes)
        $newel = $(html.trim());
        this.setElement($newel);
        $oldel.replaceWith($newel);
        this.$el.modal('show');
        var that = this;
        this.$el.on('hidden.bs.modal', function() {
            that.$el.remove();
        });
    },
    submitEvent: function(ev) {
        var data = $(ev.target).serializeArray();
        data = _.object(_.pluck(data, 'name'), _.pluck(data, 'value'));
        var d = {};
        d['title'] = data['title'];
        d['start'] = moment(data['date']+"T"+data['start']);
        d['end'] = moment(data['date']+"T"+data['end']);
        if  ( $(ev.target).has('.active *[name="course"]').length )
            d['course'] = data['course']
        var e = new Event(d);
        e.unset('comments');
        var that = this;
        e.save({}, { success: function(model, response) {
            console.log("SAVE SUCCESS");
            that.trigger("eventAdded");
            that.$el.modal('hide');
        }
        });
        return false;
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
        var $thead = $('<tr><th class="ui-time"></th></tr>')
        var that = this
        var $tbody = this.$el.find('tbody')
        var hours = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24]
        this.model.get('days').each(function(day) {
            var $header = $("<th>"+moment(day.get('date')).format('l')+"</th>").appendTo($thead)
            $header.append("&nbsp;<a href='/p/daily/"+day.get('date')+"/'><i class='fa fa-print'></i></a>")
            var ae = new AddEventButtonView({ model: new Backbone.Model({ date: day.get('date') }) })
            ae.render()
            ae.on("eventAdded", function() {
                day.fetch();
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
