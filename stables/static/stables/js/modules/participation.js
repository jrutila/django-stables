var Participation = Backbone.Model.extend({
    urlRoot: apiUrl+'participations/',
    defaults: {
        alert_level: null,
        finance_url: null,
        finance_hint: null,
        finance: null,
        rider_url: null,
        rider_name: null,
        state: 0,
    },
})

var ParticipationView = Backbone.View.extend({
    tagName: "li",
    initialize: function(data) {
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this.model, "sync", this.notifyChanged);
    },
    events: {
        'change select[name="state"]': 'stateChange',
        'change select[name="horse"]': 'horseChange',
    },
    stateChange: function(ev) {
        this.model.set('state', $(ev.target).val())
        this.$el.find('select[name="state"]').addClass('changed')
        //TODO: to model
        this.model.save()
    },
    horseChange: function(ev) {
        this.model.set('horse', $(ev.target).val())
        this.$el.find('select[name="horse"]').addClass('changed')
        //TODO: to model
        this.model.save()
    },
    notifyChanged: function(ev) {
        this.$el.find('.changed').removeClass('changed').effect("highlight", {"color": "lightGreen"}, 3000)
    },
    template: _.template($('#ParticipationView').html()),
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        $('select[name="state"]', this.$el).val(this.model.get('state'))
        $('select[name="horse"]', this.$el).val(this.model.get('horse'))
        return this
    },
})

jQuery.ui.autocomplete.prototype._resizeMenu = function () {
      var ul = this.menu.element;
        ul.outerWidth(this.element.outerWidth());
}

var userSelectorSource = []
$.get(apiUrl+"user?limit=500&format=json", "", function(data) {
    userSelectorSource = _.map(data.objects, function(u) { return u.name; })
    $(".userSelector").autocomplete("option", "source", userSelectorSource)
});

var ParticipationAdderView = Backbone.View.extend({
    tagName: "li",
    template: _.template($('#ParticipationView').html()),
    events: {
        'click button': 'submit',
        'keyUp input': function(e) {
            if (e.which === 13)
                this.submit();
        },
    },
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        var $userSelector = $("<input class='userSelector' type='text'/>").autocomplete({ source: userSelectorSource })

        this.$el.find(".ui-stbl-db-user").html($userSelector)
        this.$el.find("select[name='state']").remove()
        this.$el.append("<button><i class='icon-save' title='save'></i></button>")
    },
    submit: function() {
        this.model.set("rider_name", this.$el.find(".userSelector").val())
        this.model.set("horse", this.$el.find("select[name='horse']").val())
        var that = this
        this.model.save()
    },
})

var ParticipationCollection = Backbone.Collection.extend({
    model: Participation,
    initialize: function() {
        this.on("change:state", this.sort)
    },
    parse: function(data) {
        return _.map(data, function(d) {
            if (d.id == undefined)
            {
                delete d.id
                delete d.resource_uri
            }
            return new Participation(d);
        })
    },
    comparator: 'state',
})

var Event = Backbone.Model.extend({
    idAttribute: "start",
    parse: function(data) {
        data['participations'] = new ParticipationCollection(ParticipationCollection.prototype.parse(data['participations']))
        return data
    },
    getHour: function() {
        return parseInt(this.get('start').match(/T(\d{2})/)[1])
    },
})

var EventCollection = Backbone.Collection.extend({
    model: Event,
    url: apiUrl+'/events/',
    parse: function(data) {
        return _.map(data, function(d) { return Event.prototype.parse(d); })
    },
})


var EventView = Backbone.View.extend({
    tagName: 'div',
    initialize: function() {
        this.listenTo(this.model.get('participations'), "sort", this.render);
    },
    template: _.template($('#EventView').html()),
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        var ul = this.$el.find('ul')
        this.model.get('participations')
          .each(function(p) {
            var view = undefined
            view = new ParticipationView({model: p})
            view.render()
            ul.append(view.$el)
        }, this)
        this.renderAdder()
        return this
    },
    renderAdder: function() {
        var adder = new ParticipationAdderView({model:
            new Participation({
                event_id: this.model.get('event_id'),
                start: this.model.get('start'),
                end: this.model.get('end'),
            })
        })
        adder.render()
        this.$el.find("ul").append(adder.$el)
        var that = this
        adder.model.once("sync", function() {
            /*
            var view = new ParticipationView({model: adder.model})
            view.render()
            view.$el.find("select, span").addClass("changed")
            that.$el.find("ul").append(view.$el)
            */
            adder.remove()
            that.model.get("participations").add(this)
        })
    },
})