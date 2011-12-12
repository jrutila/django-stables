from stables.models import ParticipationTransactionActivator

def activate_transactions():
    for p in ParticipationTransactionActivator.objects.all():
        p.try_activate()

def run():
    activate_transactions()
