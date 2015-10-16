from rest_framework import viewsets
from rest_framework import serializers
from rest_framework import views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from stables.models import Participation
from stables.models import InstructorParticipation
from stables.models import Course
from stables.models import CANCELED
from datetime import datetime, date, timedelta

class UserAllowedParticipationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participation
        fields = ('id', 'state', 'participant', 'start', 'end', 'last_state_change_on', 'horse')
        read_only_fields = ('participant', 'start', 'end', 'last_state_change_on', 'horse')

class UserRestrictedParticipationSerializer(UserAllowedParticipationSerializer):
    def get_field(self, model_field):
        if model_field.name == 'state':
            model_field.editable = False
        return super(UserRestrictedParticipationSerializer, self).get_field(model_field)

class ParticipationViewSet(viewsets.ModelViewSet):
    model = Participation
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        return Participation.objects.filter(participant=user.userprofile).order_by('-start')

    def get_serializer_class(self):
        if self.suffix != 'List' and self.get_object().start > datetime.datetime.now():
            return UserAllowedParticipationSerializer
        else:
            return UserRestrictedParticipationSerializer
        return super(ParticipationViewSet, self).get_serializer_class()

class TimetableView(views.APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        start = datetime.strptime(request.QUERY_PARAMS.get('start', str(date.today())), "%Y-%m-%d").date()
        end = datetime.strptime(request.QUERY_PARAMS.get('end', str(start)), "%Y-%m-%d").date()

        dates = {}
        d = start
        while d <= end:
            from django.utils import timezone
            starttime = timezone.make_aware(datetime.combine(d, datetime.min.time()), timezone.get_current_timezone())
            endtime = timezone.make_aware(datetime.combine(d, datetime.max.time()), timezone.get_current_timezone())
            events = list(Course.objects.get_course_occurrences(starttime, endtime))
            instructors = InstructorParticipation.objects.filter(event__in=events, start__gte=starttime, end__lte=endtime).select_related()
            slots = Participation.objects.generate_participations(starttime, endtime)[1]
            dates[str(d)] = []
            for e in events:
                if e.course.api_hide:
                    continue
                occ = e.get_occurrences(starttime, endtime)
                if occ:
                    for o in occ:
                        eh = {}
                        eh['title'] = e.title
                        eh['start'] = o.start
                        eh['end'] = o.end
                        if o.original_start != o.start:
                            eh['original_start'] = o.original_start
                        if o.original_end != o.end:
                            eh['original_end'] = o.original_end
                        eh['cancelled'] = o.cancelled
                        eh['instructor'] = [ unicode(i.instructor) for i in instructors if i.event_id == e.id and i.start == o.start and i.end == o.end ]
                        if eh['instructor']:
                            eh['instructor'] = eh['instructor'][0]
                        else:
                            eh['instructor'] = None
                        if slots[o][0]:
                            eh['free_amount'] = slots[o][0].max_participants - len([ p for p in slots[o][1] if p.state != CANCELED ])
                            eh['free_slots'] = slots[o][0].max_participants > len([ p for p in slots[o][1] if p.state != CANCELED ])
                        dates[str(d)].append(eh)

            d += timedelta(days=1)
        ret = { 'start': start, 'end': end, 'dates': dates }
        return Response(ret)
