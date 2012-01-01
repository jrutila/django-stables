from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from stables.models import CoursePlugin as CoursePluginModel
from django.utils.translation import ugettext as _

class CoursePlugin(CMSPluginBase):
    model = CoursePluginModel
    text_enabled = True
    name = _('Course Plugin')
    render_template = 'stables/course_plugin.html'

    def render(self, context, instance, placeholder):
        context.update({'instance': instance})
        return context
plugin_pool.register_plugin(CoursePlugin)
