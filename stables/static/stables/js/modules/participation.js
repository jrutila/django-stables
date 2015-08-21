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
        'click .resolve': 'resolve',
        'click .confirm': 'pay',
        'click .pay': "startPay",
        'click .method': "changeMethod",
        'keyup input.method': "changeMethod",
    },
    changeMethod: function(ev) {
        var val = "";
        if ($(ev.target).is('a')) {
            val = $(ev.target).attr('data-method');
        } else if ($(ev.target).is('input')) {
            val = $(ev.target).val();
        }
        var res = this.$el.find(".resolve:first");
        var title = val ? val : res.attr("data-title");
        res.html(title.charAt(0).toUpperCase()+title.slice(1));
        res.attr("data-method", val);
        return false;
    },
    resolve: function(ev) {
        this.model.set("method", $(ev.currentTarget).attr('data-method'));
        var val = $(ev.target).attr('data-method');
        var amount = this.$el.find('.amount').val();
        this.model.set('method', val);
        this.model.set('amount', amount);
        this.model.save();
    },
    buttonClick: function(ev) {
        var trg = $(ev.target);
        var val = trg.val();
        if (val == 0)
            val = trg.parent().next().val();
        this.model.set('pay', val);
        this.model.save()
    },
    startPay: function(ev) {
        var $link = $(ev.currentTarget)
        var justConfirm = true;
        var noConfirm = false;
        if ($link.is('.pay_mobile')) {
            this.method = 'mobile'
            if (this.model.get('methods').indexOf('mobile') == -1) {
                justConfirm = false;
                $link.parent().find('[name="phone_number"]').show().focus()
            }
        } else if ($link.is('.pay_email')) {
            if (this.model.get('methods').indexOf('email') == -1) {
                justConfirm = false;
                $link.parent().find('[name="email_address"]').show().focus()
            }
            this.method = 'email'
        } else if ($link.is('.pay_manual')) {
            justConfirm = false;
            noConfirm = true;
            this.sendPaymentLink(this.model, 'manual', {}, function(data) {
                $link.after("<a href='"+data.url+"'>"+data.url+"</a>")
            });
        }
        if (justConfirm) {
            this.$el.find('.confirm_message').show();
            this.$el.find('.addinfo').hide();
        } else {
            this.$el.find('.confirm_message').hide();
        }
        !noConfirm && this.$el.find('.confirm').show();

    },
    pay: function(ev) {
        var $this = $(ev.currentTarget)
        var sendFunc = this.sendPaymentLink;
        var successFunc = function(data) {
            alert('Lähetetty!');
            $('.confirm_message, .confirm, .addinfo').hide();
        }
        var model = this.model;
        if (this.method == 'mobile') {
            console.log('Pay with mobile')
            if (this.model.get('methods').indexOf('mobile') == -1)
            {
                var pn = $this.parent().find('[name="phone_number"]').val()
                if (pn)
                    sendFunc(model, 'mobile', pn, successFunc)
            } else {
                sendFunc(model, 'mobile', undefined, successFunc)
            }
        } else if (this.method == 'email') {
            console.log('Pay with email')
            if (this.model.get('methods').indexOf('email') == -1)
            {
                var pn = $this.parent().find('[name="email_address"]').val()
                if (pn)
                    sendFunc(model, 'email', pn, successFunc)
            } else {
                sendFunc(model, 'email', undefined, successFunc)
            }
        }
        return false
    },
    sendPaymentLink: function(model, method, extra, done) {
        $.ajax({ method: 'POST', url: apiUrl+'paymentlink/',
            contentType: 'application/json',
            data: JSON.stringify({ 'method': method, 'extra': extra, 'participation_id': model.get('id') }),
            dataType: 'json',
            success: function(data) {
                done && done(data);
            }})
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
                var title = that.model.get('rider_name');
                //if (that.model.get("rider_phone"))
                    //title += "&nbsp;<a href='sms:"+that.model.get('rider_phone')+"'>sms</a>";
                title += "<button class='close'>&times;</button>";
                return title;
            },
            html: true
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
        Backbone.Do(this);
    },
    idAttribute: "id", /*function() {
        // Use this so that there can be multiple occurrences from the same event
        return this.get('event_id') + this.get('start')
    },
    */
    url: function() {
        if (this.id != undefined)
            return this.urlRoot()+this.id+'/';
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
    actions: {
        cancel: {
            url: "move/",
            method: "create",
            data: function() {
                return { cancelled: true }
            }
        },
        move: {
            url: "move/",
            method: "create",
        },
        options: {
            url: "options/",
            method: "update"
        }
    }
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
        this.listenTo(this.model, "action:cancel", this.render);
        this.listenTo(this.model, "sync", this.notifyChanged);
    },
    events: {
        'change select[name="instructor"]': 'instructorChange',
        'click a.event': 'eventClick'
    },
    template: _.template($('#EventView').html()),
    eventClick: function(ev) {
        return false;
    },
    render: function() {
        this.$el.html(this.template(this.model.attributes))
        $('select[name="instructor"]', this.$el).val(this.model.get('instructor_id'))
        var ul = this.$el.find('ul')
        var that = this;
        var model = this.model;
        this.model.get('participations')
          .each(function(p) {
            var view = undefined
            view = new ParticipationView({model: p})
            view.render()
            if (that.model.get('course_id') == null)
              view.$el.find('button').hide();
            ul.append(view.$el)
        }, this)
        if (!this.model.get('cancelled'))
            this.renderAdder()
        this.renderComments()

        var editTemplate = _.template($('#EventEditView').html());

        this.$el.find("a.event").click(function() {
            var course = new Course({id: that.model.get("course_id")});
            course.fetch().success(function() {
                var v = new EditCourseView({ model: course });
                v.render();
                v.$el.modal("show");
                v.on('courseChanged', function(course) {
                    that.trigger("courseChanged", course);
                });
            });
        });

        this.$el.find("a.move").popover({
            trigger: 'click',
            placement: 'top',
            content: function() {
                var $el = $(editTemplate(model.attributes).trim());
                $el.find("#moveeventDate").datepicker({
                    dateFormat: "yy-mm-dd",
                });
                var checkCancel = function($target)
                {
                    if ($target.is(":checked"))
                        $target.parent().siblings(":not(button)").hide();
                    else
                        $target.parent().siblings().show();
                };
                $el.find("#cancelEvent").change(function(ev) {
                    checkCancel($(ev.target));
                });
                checkCancel($el.find("#cancelEvent"));
                $el.submit(function(ev) {
                    $el.find("button").attr("disabled", "disabled");
                    $el.find("button:first").replaceWith($("#EventLoadingView").html());
                    // TODO: Okay, so we remove comments so that there is no recursion
                    that.model.unset('comments');
                    if ($("#cancelEvent").is(":checked")) {
                        if (that.model.get("cancelled") == false) {
                            that.model.cancel();
                        }
                    } else {
                        var date = $el.find("#moveeventDate").val();
                        var start = $el.find("#moveeventStart").val();
                        var end = $el.find("#moveeventEnd").val();
                        var oldStr = "";
                        oldStr += moment(that.model.get("start")).format('YYYY-MM-DDHH:mm');
                        oldStr += moment(that.model.get("end")).format('HH:mm');
                        if (date+start+end != oldStr)
                        {
                            // Something changed
                            console.log("Moving")
                            that.model.move({ start: date+"T"+start, end: date+"T"+end });
                            console.log("Moved")
                        }
                    }

                    return false;
                });
                var $that = $(this);
                $el.find("button[data-dismiss='modal']").click(function() {
                    $that.popover("toggle");
                });
                return $el;
            },
            html: true
        });
        var messageTemplate = _.template($('#MessageSendView').html());
        this.$el.find("a.message").popover({
            trigger: 'click',
            placement: 'top',
            content: function() {
                var $el = $(messageTemplate({ participations: model.get("participations").toJSON() }).trim());
                var $btn = $el.find("a.sendSms");
                $el.find("input").change(function(target, val) {
                    var href = "sms:";
                    $el.find("input:checked").each(function(chk) {
                        href += $(this).attr("data-number")+",";
                    });
                    $btn.attr("href", href);
                });
                var $that = $(this);
                $el.find("[data-dismiss='modal']").click(function() {
                    $that.popover("toggle");
                });
                return $el;
            },
            html: true
        });
        return this
    },
    instructorChange: function(ev) {
        var instrId = parseInt($(ev.target).val());
        this.$el.find('select[name="instructor"]').addClass('changed')
        // TODO: Okay, so we remove comments so that there is no recursion
        this.model.unset('comments')
        //TODO: to model
        var that = this;
        this.model.options({ instructor: instrId }, { success: function(event) {
            that.notifyChanged();
        }});
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
