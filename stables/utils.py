__author__ = 'jorutila'

def getPaymentLink(participation_id):
    from django.conf import settings
    from django.utils.importlib import import_module
    getPaymentLink = settings.PAYMENTLINK_METHOD
    func_module, func_name = getPaymentLink.rsplit('.', 1)
    mod = import_module(func_module)
    #klass = getattr(mod, class_name)
    funk = getattr(mod, func_name)
    shortUrl = funk(participation_id)
    return shortUrl
