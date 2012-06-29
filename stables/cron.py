from stables.models import ParticipationTransactionActivator, CourseTransactionActivator, CourseParticipationActivator

def activate_transactions():
    for e in CourseParticipationActivator.objects.all():
        e.try_activate()
    for p in ParticipationTransactionActivator.objects.all():
        p.try_activate()
    for c in CourseTransactionActivator.objects.all():
        c.try_activate()

def run():
    activate_transactions()
