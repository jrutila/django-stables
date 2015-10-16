from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django import forms

__author__ = 'jorutila'

class EmailAuthenticationForm(AuthenticationForm):
    def clean_username(self):
        username = self.data['username']
        if '@' in username:
            try:
                username = User.objects.get(email=username).username
            except User.DoesNotExist:
                # Let authentication framework deal with incorrect username
                pass
        return username
