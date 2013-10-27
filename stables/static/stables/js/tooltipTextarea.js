(function($) {
    $.fn.tooltipTextarea = function() {
      $("textarea", this).hide().each(function() {
        set_has_text(this);
        $(this).parent().attr('data-tooltip', $(this).val());
      });
      $(this).click(function() {
        $(this).addClass('focused');
        $("textarea", this).show().focus();
      });
      $("textarea", this).blur(function() {
        $(this).hide();
        set_has_text(this);
        $(this).parent().attr('data-tooltip', $(this).val());
      });
    }
}(jQuery))

function set_has_text(textarea)
{
  if ($(textarea).val() != '')
    $(textarea).parent().addClass('has_text');
  else
    $(textarea).parent().removeClass('has_text');
}
