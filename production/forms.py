from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

__author__ = 'jorutila'

class UnusablePasswordUserPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """
        Copied from contrib.auth
        :param email:
        :return:
        """
        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
        return active_users
