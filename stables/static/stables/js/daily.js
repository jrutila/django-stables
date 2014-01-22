$(document).ready(function() {
    $('textarea').keyup(function(data) {
        $('#note').html($(this).val())
    })

    $('.hide').click(function() {
        $(this).parents('tr.event').toggle().nextUntil('tr.event').toggle()
        return false
    })
})
