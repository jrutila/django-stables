from django.shortcuts import render
from rest_framework.reverse import reverse
from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _

def api_help(request):
    tenant = request.tenant
    api_url = reverse('timetable', request=request)
    root_url = request.build_absolute_uri('/')
    script_urls = [
            (_('Timetable'), request.build_absolute_uri(static('api-scripts/timetable.js'))),
            (_('Free slots'), request.build_absolute_uri(static('api-scripts/free_slots.js'))),
            ]
    return render(request, 'api-help/apihelp.html', {
        'tenant': tenant,
        'api_url': api_url,
        'root_url': root_url,
        'script_urls': script_urls,
        })
