from django.utils.translation import ugettext, ugettext_lazy as _

ATTENDING = 0
RESERVED = 1
SKIPPED = 2
CANCELED = 3
REJECTED = 4
WAITFORPAY = 6
PARTICIPATION_STATES = (
    (ATTENDING, ugettext('Attending')),
    (RESERVED, ugettext('Reserved')),
    (SKIPPED, ugettext('Skipped')),
    (CANCELED, ugettext('Canceled')),
    (REJECTED, ugettext('Rejected')),
)

ENROLL_STATES = (
    (WAITFORPAY, ugettext('Waiting for payment')),
    (ATTENDING, ugettext('Attending')),
    (CANCELED, ugettext('Canceled')),
    (REJECTED, ugettext('Rejected')),
    (RESERVED, ugettext('Reserved')),
)

def part_move(self, curr, prev):
    self.filter(event=prev.event, start=prev.start, end=prev.end).update(start=curr.start, end=curr.end)


from stables.models.user import *
from stables.models.financial import *
from stables.models.participations import *
#from stables.models.course import *
from stables.models.horse import *
from stables.models.accident import *
