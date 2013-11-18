var EventComment = Backbone.Model.extend({
    urlRoot: "/backbone/v1/comment/",
    defaults: {
        "comment": "kommentti",
    },
})

var EventComments = Backbone.Collection.extend({
    url: "/backbone/v1/comment/",
})

var EventCommentsManager = Backbone.Model.extend({
    defaults: {
        comments: new EventComments({}),
        last_comment: new EventComment({})
    },
})

var EventMetaData = Backbone.Model.extend({
    urlRoot: apiUrl+'eventmetadata/',
})

createMetadata = function(ev) {
    /*
    $.ajax({
        type: "POST",
        url: apiUrl+"eventmetadata/",
        data: JSON.stringify({ "end": ev.end, "event": apiUrl+'events/'+ev.event_id+'/', "start": ev.start }),
        headers: { "X-CSRFToken": Backbone.Tastypie.csrfToken },
        success: success,
        contentType: "application/json",
        dataType: "json",
    })
    */
    var em = new EventMetaData({
        start: ev.start,
        end: ev.end,
        event: apiUrl+'events/'+ev.event_id+'/',
    })
    em.save()
    return em
}

var CommentsView = Backbone.View.extend({
    model: EventCommentsManager,
    template: _.template($('#CommentsView').html()),
    initialize: function(data) {
        this.listenTo(this.model, "change", this.render);
    },
    events: {
        'keypress input[name="newcomment"]': 'newComment',
    },
    newComment: function(e) {
        if (e.which == 13)
        {
            var comment = this.$el.find('input[name="newcomment"]').val()
            if (!this.model.get('metadata'))
            {
                this.model.set('metadata', createMetadata(this.model.get('event')))
            }
            var nc = new EventComment({
                comment: comment,
                content_object: this.model.get('metadata')
            })
            nc.save()
            this.model.set('last_comment', nc)
        }
    },
    render: function() {
        this.$el.html(this.template(this.model.attributes))
    },
})
