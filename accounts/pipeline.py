from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from social_core.exceptions import AuthAlreadyAssociated
import logging

logger = logging.getLogger(__name__)

def save_user_profile(backend, user, response, *args, **kwargs):
    logger.info(f"Running save_user_profile for user {user.email if user else 'No user'}")

    if backend.name == 'google-oauth2':
        google_id = response.get('sub')
        email = response.get('email')
        full_name = response.get('name')
        phone = response.get('phone_number')  # Update the key if needed

        logger.info(f"Google ID: {google_id}, Email: {email}, Full Name: {full_name}, Phone: {phone}")

        if google_id:
            User = get_user_model()

            # Check if a user with this email exists
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(email=email, is_active=False)  # Set is_active to False by default
                logger.info(f"Created new user: {email}")

            # Update full name and phone
            if full_name:
                user.full_name = full_name
            if phone:
                user.phone = phone

            user.save()

            # Link the social account
            if not user.social_auth.filter(provider=backend.name, uid=google_id).exists():
                user.social_auth.create(provider=backend.name, uid=google_id)
                logger.info(f"Linked Google account {google_id} to user {email}")

            # Check if the user is active
            if not user.is_active:
                logger.warning(f"User {user.email} is not active. Redirecting to login with error message.")
                messages.error(backend.strategy.request, "Your account is blocked. Please contact the admin..")
                return redirect('login')  # Redirect to login page

            # Log in the user if active
            login(backend.strategy.request, user, backend='social_core.backends.google.GoogleOAuth2')
            logger.info(f"User {user.email} logged in successfully.")

            return redirect('home')  # Replace 'home' with your actual home page route name

        logger.error("Google response does not contain 'sub'.")
        return None

    return None
