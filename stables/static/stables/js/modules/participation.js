var Participation = Backbone.Model.extend({
    urlRoot: '/s/backbone/v1/participations/',
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
        this.$el.find('.changed').removeClass('changed').effect("highlight", {"color": "red"}, 3000)
    },
    template: _.template($('#ParticipationView').html()),
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        $('select[name="state"]', this.$el).val(this.model.get('state'))
        $('select[name="horse"]', this.$el).val(this.model.get('horse'))
        return this
    },
})

var ParticipationCollection = Backbone.Collection.extend({
    model: Participation,
    initialize: function() {
        this.on("change:state", this.sort)
    },
    parse: function(data) {
        console.log(data)
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
    url: '/s/backbone/v1/events/',
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
            console.log(p)
            var view = new ParticipationView({model: p})
            view.render()
            ul.append(view.$el)
        })
        return this
    },
})
