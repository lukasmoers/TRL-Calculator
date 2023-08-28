from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from trl.models import UserProfile

class guidAuthenticationBackEnd:
    """
    Custom authentication backend.

    Allows users to log in using their GUID.
    """

    def authenticate(self, request, guid=None, password=None):
        """
        Overrides the authenticate method to allow users to log in using their GUID.
        """
        try:
            user = get_user_model().objects.get(pk=guid, password=password)
            return user
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            return None

    def get_user(self, user_id):
        """
        Overrides the get_user method to allow users to log in using their GUID.
        """
        try:
            return get_user_model().objects.get(pk=user_id)
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            return None