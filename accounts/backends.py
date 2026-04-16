from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User

from . import selectors


class ClinicBackend(BaseBackend):
    """
    Custom authentication backend that validates credentials against
    the raw SQL USER table and syncs with Django's User model.
    """

    def authenticate(self, request, email=None, password=None):
        row = selectors.get_user_credentials_by_email(email)
        if not row:
            return None

        user_id, password_hash, role, first_name, last_name = row
        if not check_password(password, password_hash):
            return None

        # Get or create a Django User so Django's auth framework is satisfied.
        django_user, _ = User.objects.get_or_create(
            username=str(user_id),
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
            },
        )
        return django_user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
