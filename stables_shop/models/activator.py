from ..backends import ProductActivator
from django.db import models
from stables.models.user import RiderInfo, UserProfile
from stables.models.participations import Participation

def generate_hash():
    import itertools
    hash = ''.join(itertools.islice(chain, 12))
    return hash

class PartShortUrl(models.Model):
    participation = models.ForeignKey(Participation, unique=True)
    hash = models.CharField(unique=True, max_length=12, default=generate_hash)

    def __str__(self):
        return "%s - %s" % (self.hash, self.participation)


class EnrollProductActivator(ProductActivator):
    rider = models.ForeignKey(RiderInfo, null=True, blank=True)

    def activate(self):
        user = UserProfile.objects.find(_getUserName(self.order.shipping_address_text))

        if user:
            self.rider = user.rider
            self.product.course.enroll(user)
            self.status = self.ACTIVATED
            self.save()

class TicketProductActivator(ProductActivator):
    start = models.PositiveIntegerField(null=True)
    end = models.PositiveIntegerField(null=True)
    rider = models.ForeignKey(RiderInfo, null=True, blank=True)
    duration = models.DurationField(blank=True, null=True)

    def activate(self):
        user = UserProfile.objects.find(_getUserName(self.order.shipping_address_text))
        if user:
            self.rider = user.rider
            for i in range(0, self.product.amount):
                exp = None
                if self.product.expires:
                    exp = self.product.expires
                t = Ticket.objects.create(
                        type=self.product.ticket,
                        owner=self.rider,
                        expires=exp)
                if i == 0: self.start = t.id
                if i == self.product.amount-1: self.end = t.id
            self.duration = self.product.duration
            self.status = self.ACTIVATED
            self.save()
