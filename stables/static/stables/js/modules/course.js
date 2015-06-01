/**
 * Created by jorutila on 20.4.2015.
 */

var Course = Backbone.Model.extend({
    urlRoot: apiUrl+'courses'
});

var AddEventButtonView = Backbone.View.extend({
    tagName: 'a',
    className: 'addevent',
    events: {
        'click': 'addEvent'
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
        "submit": 'submitEvent',
        "change #addeventCourse": 'courseSelected',
        "change #addeventForm .timeform input": 'timeChanged'
    },
    timeChanged: function(ev) {
        this.addEvents = [];
        var date = this.$el.find("input[name='date']").val();
        var start = this.$el.find("input[name='start']").val();
        var end = this.$el.find("input[name='end']").val();
        var repeat = this.$el.find("input[name='repeat']").is(":checked");
        var repeatUntil = this.$el.find("input[name='repeatUntil']").val();
        var time = moment(date + " " + start);
        if (date && start && end && time) {
            this.addEvents.push(time);
            while (repeat && (
                (repeatUntil && time < moment(repeatUntil + " " + start))
                ||
                (!repeatUntil && time < moment(this.addEvents[0]).add(5*7, 'd'))
                ))
            {
                time = moment(time).add(7, 'd');
                this.addEvents.push(time);
            }
        }
        this.renderTimes();
    },
    courseSelected: function(ev) {
        var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        var $courseTab =  this.$el.find(".tab-pane:nth(1)");
        $courseTab.find(".addEventCourseInfo").html("");
        this.course = new Course({ id: $(ev.target).val() });
        var that = this;
        this.xevents = [];
        this.course.fetch({success: function(model, response) {
            var $apnd = $courseTab.find(".addEventCourseInfo").html(hExtraInfo);
            $apnd.find("input[name='default_participation_fee']").val(parseInt(model.get("default_participation_fee")));
            $apnd.find("input[name='max_participants']").val(model.get("max_participants"));
            var $enrolls = $courseTab.find(".enrolls").html("");
            _.each(model.get("enrolls"), function(e) {
                $enrolls.append("<li class='list-group-item condensed'>"+e+"</li>");
            });
            that.xevents = model.get('events');
            that.renderTimes();
        }});
    },
    renderTimes: function() {
        var $courseTab =  this.$el.find(".tab-pane:nth(1)");
        var repeat = this.$el.find("input[name='repeat']").is(":checked");
        var repeatUntil = this.$el.find("input[name='repeatUntil']").val();
        var $ul = $courseTab.find(".currentOccurrence .currentRepeat").html("");

        var $newCourseUl = this.$el.find(".tab-pane:first .currentOccurrence .currentRepeat").html("");

        var listEvents = [];
        if (!repeat)
        {
            listEvents = _.union(this.xevents, this.addEvents || []);
        } else if (this.addEvents.length > 0) {
            _.each(this.xevents, function(e) {
                if (moment(e).isBefore(this.addEvents[0], 'day'))
                    listEvents.push(e);
            },this);
            listEvents = _.union(listEvents, this.addEvents || []);
        }

        listEvents = _.map(listEvents, function(e) {
            return moment(e);
        });

        //Sort Date By Ascending Order Algorithm
        var sortByDateAsc = function (lhs, rhs)  { return lhs > rhs ? 1 : lhs < rhs ? -1 : 0; };
        listEvents.sort(sortByDateAsc);

        _.each(
            listEvents,
            function(e, i) {
                if (i >= 5) {
                    if (listEvents.length > 6) {
                        $ul.append("...");
                        $newCourseUl.append("...");
                    }
                    return;
                }
                var cl = "new";
                if (_.any(this.xevents, function(x) { return moment(x).isSame(e); }))
                    cl = "old";
            if (!repeatUntil || e.isBefore(moment(repeatUntil + " 23:59:59"))) {
                var format = "<li clasS='" + cl + "'>" + e.format("llll") + "</li>";
                $ul.append(format);
                if (cl == "new")
                    $newCourseUl.append(format);
            }
        },this);
    },
    render: function() {
        var html, $oldel=this.$el, $newel;
        this.xevents = [];
        html = _.template($('#AddEventView').html(), this.model.attributes)
        $newel = $(html.trim());
        $occ = $newel.find(".currentOccurrence")
        $occ.append(_.template($("#AddEventOccurrenceInfo").html()))
        this.setElement($newel);
        $oldel.replaceWith($newel);
        var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        $newel.find(".tab-pane:first .addEventCourseInfo").append(hExtraInfo);
        this.$el.modal('show');
        var that = this;
        this.$el.on('hidden.bs.modal', function() {
            that.$el.remove();
        });
    },
    submitEvent: function(ev) {
        this.course.save();
        return false;
        /*
        var data = $(ev.target).serializeArray();
        data = _.object(_.pluck(data, 'name'), _.pluck(data, 'value'));
        var d = {};
        d['title'] = data['title'];
        d['start'] = moment(data['date']+"T"+data['start']);
        d['end'] = moment(data['date']+"T"+data['end']);
        d['repeat'] = moment(data['repeatUntil']+"T"+data['end']);
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
        */
    },
})
