/**
 * Created by jorutila on 20.4.2015.
 */

var Course = Backbone.Model.extend({
    urlRoot: apiUrl+'courses'
});

var AddEventButtonView = Backbone.View.extend({
    events: {
        'click': 'addEvent'
    },
    addEvent: function(ev) {
        var v = new AddEventView({ 'model': this.model });
        v.render();
        var that = this;
        v.on('eventAdded', function(start) {
            that.trigger('eventAdded', start);
        });
    }
})

var EditCourseView = Backbone.View.extend({
    events: {
        "submit form": 'submitEvent',
        "click .gotoNewEvent": 'gotoNewEvent'
    },
    initialize: function(data) {
        this.date = data.date;
    },
    render: function() {
        var origName = this.model.get("name");
        var html = _.template($('#EditCourseView').html())(this.model.attributes);
        var $newel = $(html.trim());

        this.setElement($newel);

        var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        this.$el.find(".addEventCourseInfo").html(hExtraInfo(this.model.attributes));

        var that = this;
        this.$el.on('hidden.bs.modal', function() {
            that.$el.remove();
        });

        this.$el.find("[name='name']").keyup(function(ev, ui) {
            if ($(ev.target).val() != origName)
                $(ev.target).next().show();
            else
                $(ev.target).next().hide();
        });

        this.$el.modal("show");
    },
    gotoNewEvent: function() {
        var ae = new AddEventView({ 'model': new Backbone.Model({
            date: this.date,
            course: this.model,
        })})
        this.$el.modal("hide");
        ae.render();
        return false;
    },
    submitEvent: function(ev) {
        var oldname = $(ev.target).find("[name='name']").val();
        var data = $(ev.target).serializeArray();
        var default_tickets = [];
        _.each(data, function(d) {
            if (d.name == "default_tickets")
                default_tickets.push(d.value);
        });
        data = _.object(_.pluck(data, "name"), _.pluck(data, "value"));
        data.default_tickets = default_tickets;
        this.model.set(_.pick(data, "name", "max_participants", "default_participation_fee", "default_tickets", "api_hide"));
        this.model.set("api_hide", this.model.get("api_hide") == "on");
        this.model.set("name_all", true);
        var that = this;
        this.model.save(null, {
            success: function(model, response) {
                that.$el.modal('hide');
                that.trigger("courseChanged", that.model);
            }
        });
        return false;
    },
});

var AddEventView = Backbone.View.extend({
    events: {
        "submit": 'submitEvent',
        "change #addeventForm .timeform input": 'timeChanged',
        "blur .courseSelect": function(ev, ui) {
            if (!this.course || !this.course.id || this.course.get("name") != ev.target.value)
                this.courseNamed(ev,ui);

        },
        "select .courseSelect": 'courseSelected',
        "click .gotoCourseEdit": 'gotoCourseEdit'
    },
    gotoCourseEdit: function() {
        var ev = new EditCourseView({ model: this.course });
        this.$el.modal("hide");
        ev.render();
        return false;
    },
    timeChanged: function() {
        this.addEvents = [];
        var date = this.$el.find("input[name='date']").val();
        var start = this.$el.find("input[name='start']").val();
        var end = this.$el.find("input[name='end']").val();
        var repeat = this.$el.find("input[name='repeat']").is(":checked");
        var repeatUntil = this.$el.find("input[name='repeatUntil']").val();
        var time = moment(date + " " + start);
        var name = this.$el.find("input[name='name']").val();
        if (date && start && end && time) {
            if (name) this.ready(true);
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
            that.renderCourseInfo();
            var $enrolls = that.$el.find(".enrolls").html("");
            _.each(model.get("enrolls"), function(e) {
                $enrolls.append("<li class='list-group-item condensed'>"+e+"</li>");
            });
            that.xevents = model.get('events');
            that.participations = model.get('participations');
            that.renderTimes();
            that.$el.find(".gotoCourseEdit").show();
        }});
    },
    courseNamed: function(ev, ui) {
        if (!this.course || this.course.id) {
            this.course = new Course();
            this.$el.find(".courseSelect").val(ev.target.value);
            this.renderCourseInfo(true)
            this.$el.find(".enrolls").html("");
            this.participations = [];
            this.xevents = [];
            this.renderTimes();
        }
        var date = this.$el.find("input[name='date']").val();
        var start = this.$el.find("input[name='start']").val();
        var end = this.$el.find("input[name='end']").val();
        var time = moment(date + " " + start);
        if (date && start && end && time) {
            this.ready(true);
        }
    },
    renderCourseInfo: function(add) {
        if (add)
            var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        else
            var hExtraInfo = _.template($("#ShowEventCourseInfo").html());
        var $courseInfo = this.$el.find(".addEventCourseInfo").html("");
        var $apnd = $courseInfo.html(hExtraInfo(this.course.attributes));
    },
    renderTimes: function() {
        this.xparticipations = _.groupBy(this.participations, 'start');
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

        var maxPart = _.max(_.map(_.keys(this.xparticipations), function(x) { return moment(x); }));
        var minPart = _.min(_.map(_.keys(this.xparticipations), function(x) { return moment(x); }));
        var errored = false;

        _.each(
            listEvents,
            function(e, i) {
                if (!repeatUntil || e.isBefore(moment(repeatUntil + " 23:59:59"))) {
                    if (i >= 5) {
                        if (i == 5 && listEvents.length >= 6) {
                            $ul.append("<li>...</li>");
                        }
                        return;
                    }
                    var cl = "new";
                    if (_.any(this.xevents, function(x) { return moment(x).isSame(e); }))
                        cl = "old";
                    if (cl == "new" && repeat && maxPart != -Infinity && e <= maxPart) {
                        cl = "error";
                        errored = true;
                        this.ready(false);
                    }

                    var $format = this._createEvent(e, cl);

                    $ul.append($format);
                }
        },this);
        var stillLeft = _.size(this.xparticipations) > 0;
        _.each(this.xparticipations, function(xp, event) {
            $ul.append(this._createEvent(moment(event)));
        }, this);
        if (stillLeft)
            $ul.append("<li>...</li>");
    },
    _createEvent: function(e, cl) {
        var event = e.format("YYYY-MM-DDTHH:mm:ss");
        var $format = $("<li class='" + cl + "'>" + e.format("llll")+"</li>");
        if (_.has(this.xparticipations, event)) {
            var $tooltip = $("<i class='fa fa-user'></i>");
            parts = "<ul>";
            _.each(this.xparticipations[event], function(xp) {
                parts += "<li";
                if (xp.state == 3)
                    parts += " style='text-decoration: line-through'";
                parts += ">"+xp.participant+"</li>"
            });
            parts += "</ul>";
            delete this.xparticipations[event];
            $tooltip.tooltip({
                title: parts,
                html: true,
                placement: "right"
            });
            $format.append($tooltip);
        }
        return $format;
    },
    ready: function(isReady) {
        if (isReady)
            this.$el.find("button[type='submit']").removeAttr("disabled");
        else
            this.$el.find("button[type='submit']").attr("disabled", "disabled");
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
        this.$el.find(".gotoCourseEdit").hide();
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
                source: [addNewCourse].concat(coursesSource),
                select: function(ev, ui) {
                    if (ui.item.value > 0)
                        that.courseSelected(ev, ui);
                    else {
                        that.courseNamed(ev, ui);
                        return false;
                    }
                },
            }).data("ui-autocomplete")._renderMenu = function( ul, items ) {
                var that = this;
                that._renderItemData(ul, addNewCourse);
                $.each( items, function( index, item ) {
                    that._renderItemData( ul, item );
                });
        }
        // TODO: Ugghhh.. ugly
        if (this.model.get("course"))
            this.courseSelected(null, { item: { value: this.model.get("course").get("id") }});
        this.ready(false);
    },
    submitEvent: function(ev) {
        this.course = this.course || new Course();
        var data = $(ev.target).serializeArray();
        var default_tickets = [];
        _.each(data, function(d) {
            if (d.name == "default_tickets")
                default_tickets.push(d.value);
        });
        data = _.object(_.pluck(data, "name"), _.pluck(data, "value"));
        data.default_tickets = default_tickets;
        this.course.set(_.pick(data, "name", "max_participants", "default_participation_fee", "default_tickets", "api_hide"));
        this.course.set("api_hide", this.course.get("api_hide") == "on");
        this.course.set("newEvent", {
            date: data["date"],
            start: data["start"],
            end: data["end"],
            repeat: data["repeat"] == "on",
            repeatUntil: data["repeatUntil"]
        });
        var that = this;
        var isNew = this.course.get("id") != undefined;
        this.course.save(null, {
            success: function(model, response) {
                _.each(model.get("events"), function(ev) {
                    that.trigger("eventAdded", ev);
                }, this);
                that.$el.modal('hide');
                if (isNew)
                    courses.push({ value: model.get("id"), label: model.get("name")});
            }
        });
        return false;
    },
})
