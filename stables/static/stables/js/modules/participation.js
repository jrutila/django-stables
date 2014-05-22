var Participation = Backbone.Model.extend({
    urlRoot: apiUrl+'participations/',
    defaults: {
        accident_url: null,
        alert_level: null,
        finance_url: null,
        finance_hint: null,
        finance: null,
        rider_url: null,
        rider_name: null,
        state: 0,
        note: null,
        enroll: null,
    },
    initialize: function(attrs, options) {
        this.on("change:horse", this.handleHorseLimit)
        if (options && 'limits' in options)
        {
            this.limits = options['limits']
            this.handleHorseLimit()
        }
        if (options && 'horses' in options)
        {
            this.horses = options['horses'];
        }
    },
    handleHorseLimit: function() {
        var myHorse = this.get('horse')
        if (myHorse)
            myHorse = parseInt(myHorse)
        var prevHorse = this.previous('horse')
        if (prevHorse)
            prevHorse = parseInt(prevHorse)
        if (myHorse !== prevHorse)
        {
            this.limits.increase(myHorse)
            this.limits.decrease(prevHorse)
        }
    },
})
 
var Enroll = Backbone.Model.extend({
    urlRoot: apiUrl+'enroll/',
    defaults: {
        event: null,
        state: 0,
        rider: null,
    },
})

var Finance = Backbone.Model.extend({
    urlRoot: apiUrl+'financials/',
})

function changeHighlight($el) {
        $el.find('.changed').removeClass('changed').effect("highlight", {"color": "lightGreen"}, 3000)
}

var FinanceView = Backbone.View.extend({
    initialize: function(data) {
        this.listenTo(this.model, "sync", this.render);
    },
    events: {
        'click button': 'buttonClick',
    },
    buttonClick: function(ev) {
        trg = $(ev.target)
        this.model.set('pay', trg.val())
        this.model.save()
    },
    render: function() {
        this.$el.html(_.template($('#FinancePopoverView').html())(this.model.attributes))
    }
})

var ParticipationView = Backbone.View.extend({
    tagName: "li",
    initialize: function(data, options) {
        this.listenTo(this.model, "change", this.render);
        this.listenTo(this.model, "sync", this.notifyChanged);
        this.listenTo(this.model.limits, "topped", this.limitTopped);
        this.listenTo(this.model.limits, "cleared", this.limitCleared);
        this.options = options;
    },
    events: {
        'change select[name="state"]': 'stateChange',
        'change select[name="horse"]': 'horseChange',
        'change textarea[name="note"]': 'noteChange',
        'click button.enroll': 'enroll',
        'click button.denroll': 'denroll',
        'click .detail_url': 'detail_click',
        'click .note': 'note_click',
    },
    note_click: function(ev) {
        $('.detail_url', this.$el).popover('toggle')
    },
    detail_click: function(ev) {
        return false
    },
    enroll: function(ev) {
        var model = this.model
        $.msgbox("Are you sure?", {
            type: "confirm",
            buttons: [
                { type: 'submit', value: 'Yes' },
                { type: 'cancel', value: 'Cancel' },
            ],
        }, function (result) {
            if (result) {
                var e = new Enroll({
                    event: model.get('event_id'),
                    rider: model.get('rider_id'),
                })
                e.save(null, {
                    success: function() { model.fetch(); },
                    // TODO: 201 is apparently error
                    error: function() { model.fetch(); },
                })
            }
        })
    },
    denroll: function(ev) {
        var model = this.model
        $.msgbox("Are you sure?", {
            type: "confirm",
            buttons: [
                { type: 'submit', value: 'Yes' },
                { type: 'cancel', value: 'Cancel' },
            ],
        }, function (result) {
            if (result) {
                var e = new Enroll()
                e.url = model.get('enroll')
                // Id must be set so that Backbone does POST
                e.id = parseInt(model.get('enroll').split('/')[4])
                e.set('state', 3)
                e.save(null, {
                    success: function() { model.fetch(); },
                    // TODO: 201 is apparently error
                    error: function() { model.fetch(); },
                })
            }
        })
    },
    limitTopped: function(limit) {
        var horse = limit.get('horse')
        if (parseInt(this.model.get('horse')) == horse)
        {
            this.$el.find('select[name="horse"]').addClass('warning')
        }
    },
    limitCleared: function(limit) {
        var horse = limit.get('horse')
        if (parseInt(this.model.get('horse')) == horse)
        {
            this.$el.find('select[name="horse"]').removeClass('warning')
        }
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
    noteChange: function(ev) {
        var value = $(ev.target).val()
        this.model.set('note', value, { silent: true })
        //this.$el.find('textarea[name="note"]').parent('.note').addClass('changed')
        //TODO: to model
        this.model.save()
        // This is little hackish
        if (value != "")
            this.$el.find('.note i').removeClass('fa-comment-o').addClass('fa-comment')
        else
            this.$el.find('.note i').removeClass('fa-comment').addClass('fa-comment-o')
        this.$el.find('.note').attr('data-original-title', value).tooltip('fixTitle')
    },
    notifyChanged: function(ev) {
        changeHighlight(this.$el)
    },
    template: _.template($('#ParticipationView').html()),
    render: function() {
        this.$el.html(this.template(_.extend(this.model.attributes, { 'horses': this.model.horses })));
        $('select[name="state"]', this.$el).val(this.model.get('state'))
        $('select[name="horse"]', this.$el).val(this.model.get('horse'))
        var limit = this.model.limits.findLimit(parseInt(this.model.get('horse')))
        if (limit != null && limit.isTopped())
            $('select[name="horse"]', this.$el).addClass('warning')

        $('.note', this.$el).tooltip()
        var that = this
        $('.detail_url', this.$el)
        .removeAttr("title")
        .popover({
            trigger: 'click',
            placement: 'right',
            content: function() {
                var fm = new Finance({ id: that.model.get('id'), note: that.model.get('note') });
                var fv = new FinanceView({ model: fm });
                fm.fetch({ success: function() {
                    fv.render();
                }, silent: true });
                that.listenTo(fm, "sync", function() {
                    that.model.fetch()
                });
                return fv.$el;
            },
            title: function() {
                return that.model.get('rider_name') + "<button class='close'>&times;</button>";
            },
            html: true,
        }).on('shown.bs.popover', function () {
            var $thisPopover = $(this);
            $(this).next(".popover").find(".popover-title button.close").click(function() {
                $thisPopover.click();
            });
        }).tooltip({ title: this.model.get('finance_hint') })
        return this
    },
})

jQuery.ui.autocomplete.prototype._resizeMenu = function () {
      var ul = this.menu.element;
        ul.outerWidth(this.element.outerWidth());
}

var userSelectorSource = []
$.get(apiUrl+"user?limit=1000&format=json", "", function(data) {
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
        this.$el.html(this.template(_.extend(this.model.attributes, { 'horses': this.model.horses })));

        var $userSelector = $("<input class='userSelector' type='text'/>").autocomplete({ source: userSelectorSource })

        this.$el.find(".ui-stbl-db-user").html($userSelector)
        this.$el.find("select[name='state']").remove()
        this.$el.find(".note").remove()
        this.$el.append("<button><i class='fa fa-save' title='save'></i></button>")
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
    initialize: function(attrs, options) {
        this.set('comments', new EventCommentsManager({
            metadata: this.get('metadata'),
            event: this,
            last_comment: new EventComment({
                comment: this.get('last_comment'),
            })
        })
        )
        if (options != undefined)
        {
            if ('limits' in options)
            {
                this.limits = options['limits'];
                this.get('participations').each(function (p) {
                    p.limits = options['limits'];
                    p.handleHorseLimit();
                });
            }
            if ('horses' in options)
            {
                this.horses = options['horses'];
                this.get('participations').each(function (p) {
                    p.horses = options['horses'];
                });
            }
        }
    },
    idAttribute: "id", /*function() {
        // Use this so that there can be multiple occurrences from the same event
        return this.get('event_id') + this.get('start')
    },
    */
    url: function() {
        if (this.id != undefined)
            return this.urlRoot()+this.id;
        return this.urlRoot();
    },
    urlRoot: function() {
        return apiUrl+'events/';
    },
    setUrl: function() {
        return this.urlRoot()+ 'set/';
    },
    parse: function(data) {
        if ('participations' in data)
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
        this.listenTo(this.model, "sync", this.notifyChanged);
    },
    events: {
        'change select[name="instructor"]': 'instructorChange',
    },
    template: _.template($('#EventView').html()),
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        $('select[name="instructor"]', this.$el).val(this.model.get('instructor_id'))
        var ul = this.$el.find('ul')
        var that = this;
        this.model.get('participations')
          .each(function(p) {
            var view = undefined
            view = new ParticipationView({model: p})
            view.render()
            if (that.model.get('course_url') == null)
              view.$el.find('button').hide();
            ul.append(view.$el)
        }, this)
        if (!this.model.get('cancelled'))
            this.renderAdder()
        this.renderComments()
        return this
    },
    instructorChange: function(ev) {
        this.model.set('instructor_id', parseInt($(ev.target).val()))
        this.$el.find('select[name="instructor"]').addClass('changed')
        // TODO: Okay, so we remove comments so that there is no recursion
        this.model.unset('comments')
        //TODO: to model
        this.model.save()
    },
    renderComments: function() {
        if (this.comments == undefined)
            this.comments = new CommentsView({ model: this.model.get('comments') })
        this.comments.render()
        this.$el.find('.comments').html(this.comments.$el)
    },
    renderAdder: function() {
        var adder = new ParticipationAdderView({model:
            new Participation({
                event_id: this.model.get('event_id'),
                start: this.model.get('start'),
                end: this.model.get('end'),
            }, { limits: this.model.limits, horses: this.model.horses })
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
    notifyChanged: function(ev) {
        changeHighlight(this.$el)
    },
})
