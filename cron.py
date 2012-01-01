from stables.models import ParticipationTransactionActivator, CourseTransactionActivator

def activate_transactions():
    for p in ParticipationTransactionActivator.objects.all():
        p.try_activate()
    for c in CourseTransactionActivator.objects.all():
        c.try_activate()

def run():
    activate_transactions()
