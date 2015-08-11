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
        "change #addeventForm .timeform input": 'timeChanged',
        "blur .courseSelect": 'courseNamed',
        "select .courseSelect": 'courseSelected',
    },
    timeChanged: function() {
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
    courseSelected: function(ev, ui) {
        var courseId = ui.item.value;
        this.course = new Course({ id: courseId });
        var that = this;
        this.xevents = [];
        this.course.fetch({success: function(model, response) {
            that.$el.find(".courseSelect").val(model.get("name"));
            that.renderCourseInfo(model);
            var $enrolls = that.$el.find(".enrolls").html("");
            _.each(model.get("enrolls"), function(e) {
                $enrolls.append("<li class='list-group-item condensed'>"+e+"</li>");
            });
            that.xevents = model.get('events');
            that.renderTimes();
        }});
    },
    courseNamed: function(ev, ui) {
        if (!this.course) {
            this.course = new Course();
            this.renderCourseInfo()
        }
    },
    renderCourseInfo: function(model) {
        var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        var $courseInfo = this.$el.find(".addEventCourseInfo").html("");
        var $apnd = $courseInfo.html(hExtraInfo);
        if (model) {
            $apnd.find("input[name='default_participation_fee']").val(parseInt(model.get("default_participation_fee")));
            $apnd.find("input[name='max_participants']").val(model.get("max_participants"));
        }
    },
    renderTimes: function() {
        var repeat = this.$el.find("input[name='repeat']").is(":checked");
        var repeatUntil = this.$el.find("input[name='repeatUntil']").val();
        var $ul = this.$el.find(".currentOccurrence .currentRepeat").html("");

        var listEvents = [];
        if (!repeat)
        {
            listEvents = _.union(this.xevents, this.addEvents || []);
        } else {

            if (this.addEvents.length > 0) {
                _.each(this.xevents, function (e) {
                    if (moment(e).isBefore(this.addEvents[0], 'day'))
                        listEvents.push(e);
                }, this);
                listEvents = _.union(listEvents, this.addEvents || []);
            } else {
                listEvents = _.union(this.xevents, this.addEvents || []);
            }
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
                if (!repeatUntil || e.isBefore(moment(repeatUntil + " 23:59:59"))) {
                    if (i >= 5) {
                        if (i == 5 && listEvents.length >= 6) {
                            $ul.append("...");
                        }
                        return;
                    }
                    var cl = "new";
                    if (_.any(this.xevents, function(x) { return moment(x).isSame(e); }))
                        cl = "old";

                    var format = "<li class='" + cl + "'>" + e.format("llll") + "</li>";
                    $ul.append(format);
                }
        },this);
    },
    tabSelected: function($newTab) {
        var $inputs = $newTab.find("input, label");
        $inputs.show();
        var id = $newTab.attr("id");
        switch (id)
        {
            case "onetime-tab":
                $newTab.find("[for='addeventRepeat'],[id='addeventRepeat']").hide();
                $newTab.find("[for='addeventRepeatUntil'],[id='addeventRepeatUntil']").hide();
                $newTab.find("[id='addeventRepeat']").prop("checked", false);
                $newTab.find("[id='addeventRepeatUntil']").val("");
                this.timeChanged();
                this.renderTimes();
                break;
            case "repeating-tab":
                $newTab.find("[for='addeventRepeat'],[id='addeventRepeat']").hide();
                $newTab.find("[id='addeventRepeat']").prop("checked", true);
                $newTab.find("[id='addeventRepeatUntil']").val("");
                this.timeChanged();
                this.renderTimes();
                break;
            case "ending-tab":
                $newTab.find("[for='addeventDate'],[id='addeventDate']").hide();
                $newTab.find("[for='addeventStart'],[id='addeventStart']").hide();
                $newTab.find("[for='addeventEnd'],[id='addeventEnd']").hide();
                $newTab.find("[for='addeventRepeat'],[id='addeventRepeat']").hide();
                $newTab.find("[id='addeventRepeat']").prop("checked", false);
                $newTab.find("[id^='addevent']:not([id='addeventDate'])").val("");
                this.timeChanged();
                this.renderTimes();
                break;
        }
    },
    render: function() {
        var html, $oldel=this.$el, $newel;
        this.xevents = [];
        this.addEvents = [];
        html = _.template($('#AddEventView').html())(this.model.attributes);
        $newel = $(html.trim());

        this.setElement($newel);
        $oldel.replaceWith($newel);
        this.$el.modal('show');

        this.$timeform = this.$el.find(".timeform");
        //this.$timeform.find("#addeventDate").datepicker($.datepicker.regional[ "fi" ] );
        this.$timeform.find("#addeventDate, #addeventRepeatUntil")
            .datepicker({
                dateFormat: "yy-mm-dd",
                showAnim: "slideDown",
            });

        var that = this;
        this.$el.on('hidden.bs.modal', function() {
            that.$el.remove();
        });

        this.$el.find('a[data-toggle="tab"]').on('show.bs.tab', function(e) {
            var $oldTab = $($(e.relatedTarget).attr("href"));
            var $newTab = $($(e.target).attr("href"));
            $oldTab.children().appendTo($newTab);
            that.tabSelected($newTab);
        });
        this.tabSelected(that.$el.find("#onetime-tab"));

        var coursesSource = courses;

        $newel.find(".courseSelect")
            .autocomplete({
                source: coursesSource,
                select: function(ev, ui) { that.courseSelected(ev, ui); }
            });
    },
    submitEvent: function(ev) {
        this.course = this.course || new Course();
        var data = $(ev.target).serializeArray();
        data = _.object(_.pluck(data, "name"), _.pluck(data, "value"));
        this.course.set(_.pick(data, "name", "max_participants", "default_participation_fee"))
        this.course.set("newEvent", {
            date: data["date"],
            start: data["start"],
            end: data["end"],
            repeat: data["repeat"] == "on",
            repeatUntil: data["repeatUntil"]
        });
        this.course.save();
        return false;
        /*
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
