$(document).ready(function() {
  $("textarea[name$='note']").hide().wrap("<div class='note'></div>").each(function() {
    set_has_text(this);
    $(this).parent().attr('data-tooltip', $(this).val());
  });
  $("div.note").click(function() {
    $(this).addClass('focused');
    $("textarea", this).show().focus();
  });
  $("textarea[name$='note']").blur(function() {
    $(this).hide();
    set_has_text(this);
    $(this).parent().attr('data-tooltip', $(this).val());
  });
  $("select[name$='state']").change(function() {
    $(this).addClass('changed');
  });
  $("select[name$='horse']").change(function() {
    $(this).addClass('changed');
  });
  $("select[name$='instructor']").change(function() {
    $(this).addClass('changed');
  });

  /* Hide unattending */
  $('#show_hidden').change(function() {
    $('li.hiddable').toggle()
  })
  if (!$('#show_hidden').is(':checked'))
    $('li.hiddable').hide()
});

function set_has_text(textarea)
{
  if ($(textarea).val() != '')
    $(textarea).parent().addClass('has_text');
  else
    $(textarea).parent().removeClass('has_text');
}
