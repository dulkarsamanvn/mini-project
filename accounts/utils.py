import random
from django.core.cache import cache
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    return random.randint(100000, 999999)

def send_otp(email, otp):
    subject = "Your OTP for Account Verification"
    message = f"Your OTP is: {otp}"
    send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
