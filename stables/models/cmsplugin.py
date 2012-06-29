from django.db import models
from cms.models import CMSPlugin
class CoursePlugin(CMSPlugin):
    class Meta:
        app_label = "stables"

    def __unicode__(self):
        cnt = self.courses.count()
        if cnt > 1:
            return str(cnt)
        return self.courses.all()[0].__unicode__()

    courses = models.ManyToManyField('stables.Course', related_name='plugins')

    def copy_relations(self, oldinstance):
        self.courses = oldinstance.courses.all()
