from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse_lazy
from django.views.generic import RedirectView

class DefaultRedirectView(RedirectView):
    def get_redirect_url(self, **kwargs):
        return reverse_lazy('user_default')

class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

def confirm_required(template_name, context_creator, key='__confirm__'):
    """
    Decorator for views that need confirmation page. For example, delete
    object view. Decorated view renders confirmation page defined by template
    'template_name'. If request.POST contains confirmation key, defined
    by 'key' parameter, then original view is executed.

    Context for confirmation page is created by function 'context_creator',
    which accepts same arguments as decorated view.

    Example
    -------

        def remove_file_context(request, id):
            file = get_object_or_404(Attachment, id=id)
            return RequestContext(request, {'file': file})

        @confirm_required('remove_file_confirm.html', remove_file_context)
        def remove_file_view(request, id):
            file = get_object_or_404(Attachment, id=id)
            file.delete()
            next_url = request.GET.get('next', '/')
            return HttpResponseRedirect(next_url)

    Example of HTML template
    ------------------------

        <h1>Remove file {{ file }}?</h1>

        <form method="POST" action="">
            <input type="hidden" name="__confirm__" value="1" />
            <input type="submit" value="delete"/> <a href="{{ file.get_absolute_url }}">cancel</a>
        </form>

    """
    def decorator(func):
        def inner(view, request, *args, **kwargs):
            if request.POST.has_key(key):
                return func(view, request, *args, **kwargs)
            else:
                context = context_creator and context_creator(request, *args, **kwargs) \
                    or RequestContext(request)
                return render_to_response(template_name, context)
        return wraps(func)(inner)
    return decorator
