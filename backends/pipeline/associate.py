from django.core.exceptions import MultipleObjectsReturned

from social_auth.utils import setting
from social_auth.models import User
from social_auth.backends.pipeline import warn_setting
from social_auth.backends.exceptions import AuthException


def associate_by_name_and_empty_email(details, *args, **kwargs):
    """Return user entry with same email address as one returned on details."""
    email = details.get('email')
    first_name = details.get('first_name')
    last_name = details.get('last_name')

    try:
        return {'user': User.objects.get(email='', first_name=first_name, last_name=last_name)}
    except MultipleObjectsReturned:
        raise AuthException(kwargs['backend'], 'Not unique name or email is set.')
    except User.DoesNotExist:
        pass
