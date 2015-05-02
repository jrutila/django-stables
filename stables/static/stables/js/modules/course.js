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
        "change #addeventCourse": 'courseSelected'
    },
    courseSelected: function(ev) {
        var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        var $courseTab =  this.$el.find(".tab-pane:nth(1)");
        $courseTab.find(".addEventCourseInfo").html("");
        this.course = new Course({ id: $(ev.target).val() });
        this.course.fetch({success: function(model, response) {
            var $apnd = $courseTab.find(".addEventCourseInfo").html(hExtraInfo);
            console.log(model);
            $apnd.find("input[name='default_participation_fee']").val(parseInt(model.get("default_participation_fee")));
            $apnd.find("input[name='max_participants']").val(model.get("max_participants"));
        }});
    },
    render: function() {
        var html, $oldel=this.$el, $newel;
        html = _.template($('#AddEventView').html(), this.model.attributes)
        $newel = $(html.trim());
        this.setElement($newel);
        $oldel.replaceWith($newel);
        //var hExtraInfo = _.template($("#AddEventCourseInfo").html());
        //$newel.find(".tab-pane:first").append(hExtraInfo);
        this.$el.modal('show');
        var that = this;
        this.$el.on('hidden.bs.modal', function() {
            that.$el.remove();
        });
    },
    submitEvent: function(ev) {
        this.course.save()
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
