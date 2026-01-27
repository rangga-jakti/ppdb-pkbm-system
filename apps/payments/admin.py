"""
Django Admin configuration untuk Payments.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Payment, PaymentLog


class PaymentLogInline(admin.TabularInline):
    """Inline admin untuk Payment Logs"""
    model = PaymentLog
    extra = 0
    readonly_fields = ['event_type', 'old_status', 'new_status', 'signature_valid', 'created_at']
    fields = ['created_at', 'event_type', 'old_status', 'new_status', 'signature_valid', 'error_message']
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin untuk Payments"""
    
    list_display = [
        'gateway_order_id',
        'registration_link',
        'user_email',
        'total_amount',
        'status_badge',
        'payment_method',
        'created_at',
        'paid_at',
    ]
    
    list_filter = [
        'status',
        'payment_method',
        'created_at',
        'paid_at',
    ]
    
    search_fields = [
        'gateway_order_id',
        'gateway_transaction_id',
        'va_number',
        'registration__registration_number',
        'registration__full_name',
        'user__email',
    ]
    
    readonly_fields = [
        'registration',
        'user',
        'gateway_order_id',
        'gateway_transaction_id',
        'va_number',
        'payment_method',
        'amount',
        'admin_fee',
        'total_amount',
        'created_at',
        'updated_at',
        'paid_at',
        'expires_at',
        'gateway_response_display',
    ]
    
    fieldsets = (
        (_('Payment Info'), {
            'fields': (
                'gateway_order_id',
                'gateway_transaction_id',
                'status',
            )
        }),
        (_('Related Objects'), {
            'fields': (
                'registration',
                'user',
            )
        }),
        (_('Payment Details'), {
            'fields': (
                'payment_method',
                'va_number',
                'amount',
                'admin_fee',
                'total_amount',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
                'paid_at',
                'expires_at',
            )
        }),
        (_('Gateway Response'), {
            'fields': (
                'gateway_response_display',
            ),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [PaymentLogInline]
    
    def status_badge(self, obj):
        """Display status dengan warna"""
        colors = {
            'PENDING': 'orange',
            'PAID': 'green',
            'EXPIRED': 'gray',
            'FAILED': 'red',
            'REFUNDED': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def registration_link(self, obj):
        """Link ke registration"""
        url = reverse('admin:registration_studentregistration_change', args=[obj.registration.id])
        return format_html('<a href="{}">{}</a>', url, obj.registration.registration_number)
    registration_link.short_description = 'Registration'
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    
    def gateway_response_display(self, obj):
        """Display gateway response sebagai JSON formatted"""
        if obj.gateway_response:
            import json
            formatted = json.dumps(obj.gateway_response, indent=2)
            return format_html('<pre>{}</pre>', formatted)
        return '-'
    gateway_response_display.short_description = 'Gateway Response'
    
    def has_add_permission(self, request):
        """Disable manual payment creation via admin"""
        return False


@admin.register(PaymentLog)
class PaymentLogAdmin(admin.ModelAdmin):
    """Admin untuk Payment Logs (Read-only)"""
    
    list_display = [
        'created_at',
        'payment_order_id',
        'event_type',
        'old_status',
        'new_status',
        'signature_valid',
        'ip_address',
    ]
    
    list_filter = [
        'event_type',
        'signature_valid',
        'created_at',
    ]
    
    search_fields = [
        'payment__gateway_order_id',
        'ip_address',
        'error_message',
    ]
    
    readonly_fields = [
        'payment',
        'event_type',
        'old_status',
        'new_status',
        'signature_valid',
        'request_data',
        'response_data',
        'error_message',
        'ip_address',
        'user_agent',
        'created_at',
    ]
    
    fields = readonly_fields
    
    def payment_order_id(self, obj):
        """Display payment order ID"""
        return obj.payment.gateway_order_id
    payment_order_id.short_description = 'Order ID'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False