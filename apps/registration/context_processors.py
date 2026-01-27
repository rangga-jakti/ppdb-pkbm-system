"""
Context processors untuk registration app.
Data ini akan tersedia di semua templates.
"""
from django.conf import settings


def registration_settings(request):
    """
    Make registration-related settings available in templates.
    """
    return {
        'REGISTRATION_FEE': settings.REGISTRATION_FEE,
        'PAYMENT_MERCHANT_NAME': settings.PAYMENT_MERCHANT_NAME,
        'PAYMENT_EXPIRY_HOURS': settings.PAYMENT_EXPIRY_HOURS,
    }
    

def contact_info(request):
    """Make contact info available in all templates"""
    return {
        'contact': settings.CONTACT_INFO
    }