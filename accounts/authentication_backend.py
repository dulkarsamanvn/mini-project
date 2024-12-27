# authentication_backend.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser

class EmailBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            # Try to get the user by email
            user = CustomUser.objects.get(email=email)
            if user.check_password(password):
                return user  # Return the user if password is correct
        except CustomUser.DoesNotExist:
            return None
        return None  # Return None if authentication fails

    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return None
