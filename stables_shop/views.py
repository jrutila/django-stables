from django import forms
from django.forms import HiddenInput
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
import django_settings
from shop.util.order import add_order_to_request
from shop.views.checkout import CheckoutSelectionView
from shop.models import AddressModel
from django.views.generic.base import TemplateView
from django.views.generic import UpdateView, DetailView, View
from django.views.generic import CreateView
from django.views.generic import FormView
from django.views.generic import ListView
from django.views.generic import RedirectView
from shop.models import Order
from shop.models import Product
from stables_shop.backends import DigitalShipping
from stables.models import UserProfile, Participation, pay_participation
from django.forms.util import ErrorList
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from crispy_forms.layout import ButtonHolder
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import MultipleObjectsReturned, ValidationError
from models import PartShortUrl
import paytrail
from shop.backends_pool import backends_pool

class DefaultHelper(FormHelper):
    label_class = "col-xs-2"
    field_class = "col-xs-10"
    form_tag = False
    form_class = "row"
    disable_csrf = True

def ret_name(self):
    return self.name

funcType = type(AddressModel.as_text)

class NoShippingForm(forms.ModelForm):
    class Meta:
        model = AddressModel
        fields = ['name', 'phone_number' ]

    def save(self):
        obj = super(forms.ModelForm, self).save()
        #obj.as_text = funcType(ret_name, obj, AddressModel)
        return obj

class FinnishPaymentForm(forms.ModelForm):
    class Meta:
        model = AddressModel
        fields = ['name', 'phone_number' ]

    def save(self):
        obj = super(forms.ModelForm, self).save()
        return obj

class NoShippingAddressCheckoutSelectionView(CheckoutSelectionView):
    def get_shipping_form_class(self):
        return NoShippingForm

    def get_billing_form_class(self):
        return FinnishPaymentForm

    def get_shipping_address_form(self):
        form = super(NoShippingAddressCheckoutSelectionView, self).get_shipping_address_form()
        form.helper = DefaultHelper()
        return form

    def get_billing_address_form(self):
        form = super(NoShippingAddressCheckoutSelectionView, self).get_billing_address_form()
        form.helper = DefaultHelper()
        return form

    def get_extra_info_form(self):
        form = super(NoShippingAddressCheckoutSelectionView, self).get_extra_info_form()
        form.helper = DefaultHelper()
        return form

    def get_billing_backends_choices(self):
        billing_backends = backends_pool.get_payment_backends_list()
        return tuple([(x.url_namespace, getattr(x, 'backend_verbose_name', x.backend_name)) for x in billing_backends])

    def get_billing_and_shipping_selection_form(self):
        form = super(NoShippingAddressCheckoutSelectionView, self).get_billing_and_shipping_selection_form()
        form.fields['shipping_method'].widget.attrs['class'] = "hidden"
        form.fields['shipping_method'].label = ""
        choices = self.get_billing_backends_choices()
        tpl = []
        for c in choices:
            if c[0] == 'paytrail-payment' \
                    and django_settings.get('merchant_id') != "":
                tpl.append(c)
            #and django_settings.exists['payment_account_number']\
            if c[0] == 'advance-payment' \
                    and django_settings.get('payment_account_number') != "":
                tpl.append(c)
        form.fields['payment_method'] = forms.ChoiceField(choices=tpl, label=_('Payment method'))
        form.helper = DefaultHelper()
        return form

class ShopRedirectView(RedirectView):
    def get_redirect_url(self):
        return reverse('product_list')

class InfoView(TemplateView):
    template_name = 'stables_shop/info.html'

    def get_context_data(self, **kwargs):
        context = super(InfoView, self).get_context_data(**kwargs)
        context['content'] = django_settings.get('shop_info')
        return context

class ParticipationPayForm(forms.Form):
    participation_id = forms.fields.IntegerField(widget=HiddenInput)

def _check_authcode(self, request):
    order_number = request.GET.get('ORDER_NUMBER')
    timestamp = request.GET.get('TIMESTAMP')
    paid = request.GET.get('PAID')
    method = request.GET.get('METHOD')
    authCode = paytrail.calcAuthCode(order_number, timestamp, paid, method)
    if authCode != request.GET.get('RETURN_AUTHCODE').lower():
        raise Exception("Authcode mismatch!")
    return order_number

class ParticipationPaymentNotify(View): # DetailView):
    def get(self, request, *args, **kwargs):
        part_id = _check_authcode(self, self.request)
        object = PartShortUrl.objects.get(hash=self.kwargs['hash']).participation
        if str(object.id) != part_id:
            raise Exception("Authcode mismatch!")
        pay_participation(object, object.get_saldo()[2], method='paytrail')
        return HttpResponse('ok')

class ParticipationPaymentFailure(TemplateView): # DetailView):
    pass

class ParticipationPaymentSuccess(TemplateView): # DetailView):
    template_name = 'stables_shop/pay_participation.html'

    def get_context_data(self, **kwargs):
        ctx = super(ParticipationPaymentSuccess, self).get_context_data(**kwargs)
        part_id = _check_authcode(self, self.request)
        ctx['object'] = PartShortUrl.objects.get(hash=self.kwargs['hash']).participation
        if str(ctx['object'].id) != part_id:
            raise Exception("Authcode mismatch!")
        ctx['paid'] = True
        return ctx

class ParticipationPaymentRedirect(RedirectView):
    permanent = False
    def get_redirect_url(self, **kwargs):
        part = Participation.objects.get(id=self.kwargs['id'])
        # TODO: Check rights for the participation
        pshr = PartShortUrl.objects.create(participation=part)
        return reverse('shop-pay', kwargs={'hash': pshr.hash })

class ParticipationPayment(FormView): # DetailView):
    template_name = 'stables_shop/pay_participation.html'
    model = Participation
    form_class = ParticipationPayForm

    def get_initial(self):
        initial = super(ParticipationPayment, self).get_initial()
        self.object = PartShortUrl.objects.get(hash=self.kwargs['hash']).participation
        initial['participation_id'] = self.object.id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super(ParticipationPayment, self).get_context_data(**kwargs)
        ctx['object'] = self.object
        ctx['total'] = self.object.get_saldo()[0] * -1
        return ctx

    def form_valid(self, form):
        user = self.object.participant.user
        from decimal import Decimal
        order_total = self.object.get_saldo()[0] * -1
        urls = {
            'success': self.request.build_absolute_uri(reverse('shop-pay-success', kwargs=self.kwargs)),
            'notification': self.request.build_absolute_uri(reverse('shop-pay-notify', kwargs=self.kwargs)),
            'failure': self.request.build_absolute_uri(reverse('shop-pay-failure', kwargs=self.kwargs)),
            'pending': ''
        }
        order = Order()
        order.id = self.object.id
        order.order_total = order_total
        self.success_url = paytrail.createPayment(order,order_total,order.id,urls)
        return super(ParticipationPayment, self).form_valid(form)

_products = None
def products():
    global _products
    if _products == None:
        _products = {}
        for ct in ContentType.objects.filter(app_label='stables_shop'):
            if issubclass(ct.model_class(), Product):
                _products[ct.model_class()] = ct
    return _products

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

class ShopEditorMixin(object):
    @method_decorator(permission_required('shop.change_product'))
    def dispatch(self, request, *args, **kwargs):
        return super(ShopEditorMixin, self).dispatch(request, *args, **kwargs)

class ShopSettingsSetMixin(object):
    def dispatch(self, request, *args, **kwargs):
        setform = SettingsForm()
        for f in setform.fields:
            if f not in setform.initial:
                return redirect(reverse("shop-settings"))
        return super(ShopSettingsSetMixin, self).dispatch(request, *args, **kwargs)

class HomePageView(ShopEditorMixin, ShopSettingsSetMixin, TemplateView):
    template_name = "stables_shop/index.html"

    def get_context_data(self, **kwargs):
        context = super(HomePageView, self).get_context_data(**kwargs)
        orders = Order.objects.exclude(status=Order.CANCELED).exclude(status=Order.SHIPPED).order_by('-status', 'id')\
            .prefetch_related('orderpayment_set', 'items')
        orders = list(orders)
        for o, val in enumerate(orders):
            orders[o].ship_help = val.shipping_address_text.split('\n') if val.shipping_address_text else []
        context['orders'] = orders
        context['products'] = Product.objects.all().order_by('-active', 'name')
        context['newproducts'] = products()
        return context

class DefaultForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.helper = DefaultHelper()
        self.helper.add_input(Submit('submit', 'Submit'))
        self.helper.form_tag = True
        self.helper.disable_csrf = False

def _getAddressText(data):
    addr = AddressModel()
    addr.name = data['name']
    addr.phone_number = data['phone_number']
    return addr.as_text()

class ShipForm(DefaultForm):
    order = forms.ModelChoiceField(queryset=Order.objects.all(), widget=forms.HiddenInput)
    target = forms.ModelChoiceField(queryset=UserProfile.objects.all())
    name = forms.CharField(required=False)
    phone_number = forms.CharField(required=False)

    def clean(self):
        data = super(ShipForm, self).clean()
        if 'target' not in data:
            if 'name' in data:
                data['order'].shipping_address_text = _getAddressText(data)
                data['order'].save()
            try:
                data['target'] = UserProfile.objects.find(data['name'])
                del self.errors['target']
            except UserProfile.DoesNotExist:
                self.errors['target'] = ErrorList(
                        [_('User "%s" not found') % data['order'].shipping_address_text])
            except MultipleObjectsReturned:
                self.errors['target'] = ErrorList(
                        [_('User "%s" is too ambiguous') % data['order'].shipping_address_text])
        else:
            data['name'] = "%s %s" % (data['target'].user.first_name, data['target'].user.last_name)
            data['order'].shipping_address_text = _getAddressText(data)
            data['order'].save()
        return data


def prodform(prodmodel):
    class ProductForm(forms.ModelForm):
        class Meta:
            model = prodmodel

        def __init__(self, *args, **kwargs):
            super(ProductForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper(self)
            self.helper.form_tag = True
            self.helper.disable_csrf = False
            self.helper.layout.append(
                      ButtonHolder(
                        Submit('save', _('Save')),
                        )
                    )
    return ProductForm


class EditProduct(ShopEditorMixin, UpdateView):
    model = Product
    template_name = "stables_shop/generic_form.html"
    success_url = '/s' #TODO: Bad!
    def get_form_class(self):
        return prodform(self.object.__class__)

class CreateProduct(ShopEditorMixin, CreateView):
    model = Product
    template_name = "stables_shop/generic_form.html"
    success_url = '/s' #TODO: Bad!

    def get_form_class(self):
        ct = ContentType.objects.get(pk=self.kwargs['content_type_id'])
        return prodform(ct.model_class())

class FinishedOrderList(ShopEditorMixin, ListView):
    model = Order
    template_name = "stables_shop/order_list.html"
    context_object_name = 'order_list'

    queryset = Order.objects.all().order_by('-id')

class PayForm(DefaultForm):
    order = forms.ModelChoiceField(queryset=Order.objects.all())
    amount = forms.DecimalField(localize=True)
    transaction_id = forms.CharField()
    payment_method = forms.CharField()

class OrderCancelMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if (request.POST.get("cancel") != None):
            o = Order.objects.get(pk=request.POST.get("order"))
            o.status = Order.CANCELED
            o.save()
            return HttpResponseRedirect(reverse('shop-home'))
        return super(OrderCancelMixin, self).dispatch(request, *args, **kwargs)

class PayView(ShopEditorMixin, OrderCancelMixin, FormView):
    template_name = 'stables_shop/generic_form.html'
    success_url = '/s' #TODO: Bad!
    form_class = PayForm

    def form_valid(self, form):
        from shop.payment import api
        api.PaymentAPI().confirm_payment(
                form.cleaned_data['order'],
                form.cleaned_data['amount'],
                form.cleaned_data['transaction_id'],
                form.cleaned_data['payment_method'],
                )
        return super(PayView, self).form_valid(form)

class ShipView(ShopEditorMixin, OrderCancelMixin, FormView):
    template_name = 'stables_shop/generic_form.html'
    success_url = '/s' #TODO: Bad!
    form_class = ShipForm

    def form_valid(self, form):
        from shop.shipping import api
        DigitalShipping(api.ShippingAPI()).ship(form.cleaned_data['order'])
        return super(ShipView, self).form_valid(form)


class SettingsForm(DefaultForm):
    shop_name = forms.CharField(help_text=_("Name of the shop shown in left upper corner"))
    shop_homepage = forms.CharField(help_text=_("Address for the main page (e.g. your homepage)"))
    shop_theme = forms.ChoiceField(choices=(('cerulean', 'cerulean'), ('amelia', 'amelia')))
    shop_info = forms.CharField(help_text=_("Text that is visible on shop info page"), widget=forms.Textarea, max_length=2000)

    payment_account_number = forms.CharField(help_text=_("Your bank account number"), required=False)
    payment_receiver = forms.CharField(help_text=_("Invoice receiver name"), required=False)

    merchant_id = forms.CharField(help_text=_("Your Paytrail merchant id"), required=False)
    merchant_pass = forms.CharField(help_text=_("Your Paytrail merchant secret"), required=False)

    def __init__(self, *args, **kwargs):
        initial = django_settings.all()
        kwargs['initial'] = initial
        return super(SettingsForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(SettingsForm, self).clean()
        pan = cleaned_data.get('payment_account_number')
        pr = cleaned_data.get('payment_receiver')
        mi = cleaned_data.get('merchant_id')
        mp = cleaned_data.get('merchant_pass')
        if bool(pan) != bool(pr):
            msg = _('Both payment account number and payment receiver must be set')
            self._errors['payment_account_number'] = self.error_class([msg])
            self._errors['payment_receiver'] = self.error_class([msg])
        if bool(mi) != bool(mp):
            msg = _('Both merchant id and secret must be set')
            self._errors['merchant_id'] = self.error_class([msg])
            self._errors['merchant_pass'] = self.error_class([msg])
        return cleaned_data

    def save(self):
        for f in self.fields:
            value = self.cleaned_data.get(f)
            if value:
                t = 'String'
                if (len(value) > 254):
                    t = 'LongString'
                django_settings.set(t, f, value)
            else:
                django_settings.set('String', f, '', validate=False)

class SettingsView(ShopEditorMixin, FormView):
    template_name = 'stables_shop/generic_form.html'
    success_url = '/s' #TODO: Bad!
    form_class = SettingsForm

    def form_valid(self, form):
        form.save()
        return super(SettingsView, self).form_valid(form)
