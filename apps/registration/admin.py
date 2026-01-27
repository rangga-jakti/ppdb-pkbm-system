"""
Django Admin configuration untuk Registration.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import StudentRegistration, Document


class DocumentInline(admin.TabularInline):
    """Inline admin untuk Documents"""
    model = Document
    extra = 0
    readonly_fields = ['document_type', 'original_filename', 'file_size', 'uploaded_at', 'is_verified']
    fields = ['document_type', 'file', 'original_filename', 'file_size', 'is_verified', 'verification_notes']
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    """Admin untuk Student Registration"""
    
    list_display = [
        'registration_number',
        'full_name',
        'nisn',
        'academic_year',
        'program_choice',
        'status_badge',
        'payment_status',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'academic_year',
        'program_choice',
        'created_at',
        'submitted_at',
    ]
    
    search_fields = [
        'registration_number',
        'full_name',
        'nisn',
        'user__email',
        'parent_name',
        'parent_phone',
    ]
    
    readonly_fields = [
        'registration_number',
        'user',
        'created_at',
        'updated_at',
        'submitted_at',
        'verified_at',
        'verified_by',
    ]
    
    fieldsets = (
        (_('Registration Info'), {
            'fields': (
                'registration_number',
                'user',
                'academic_year',
                'status',
            )
        }),
        (_('Student Data'), {
            'fields': (
                'full_name',
                'nisn',
                'birth_place',
                'birth_date',
                'gender',
            )
        }),
        (_('Previous School'), {
            'fields': (
                'previous_school',
                'previous_school_npsn',
                'graduation_year',
                'program_choice',
            )
        }),
        (_('Address'), {
            'fields': (
                'address',
                'city',
                'province',
                'postal_code',
            )
        }),
        (_('Parent/Guardian'), {
            'fields': (
                'parent_name',
                'parent_phone',
            )
        }),
        (_('Verification'), {
            'fields': (
                'verified_by',
                'verified_at',
                'verification_notes',
            )
        }),
        (_('Timestamps'), {
            'fields': (
                'created_at',
                'updated_at',
                'submitted_at',
            )
        }),
    )
    
    inlines = [DocumentInline]
    
    def status_badge(self, obj):
        """Display status dengan warna"""
        colors = {
            'DRAFT': 'gray',
            'SUBMITTED': 'blue',
            'PAID': 'orange',
            'VERIFIED': 'green',
            'REJECTED': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status(self, obj):
        """Display payment status"""
        if hasattr(obj, 'payment'):
            payment = obj.payment
            if payment.status == 'PAID':
                return format_html(
                    '<span style="color: green;">✓ Lunas</span>'
                )
            elif payment.status == 'PENDING':
                return format_html(
                    '<span style="color: orange;">⏳ Pending</span>'
                )
            else:
                return format_html(
                    '<span style="color: red;">✗ {}</span>',
                    payment.get_status_display()
                )
        return format_html('<span style="color: gray;">-</span>')
    payment_status.short_description = 'Payment'


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin untuk Documents"""
    
    list_display = [
        'document_type',
        'registration_link',
        'original_filename',
        'file_size_display',
        'is_verified',
        'uploaded_at',
    ]
    
    list_filter = [
        'document_type',
        'is_verified',
        'uploaded_at',
    ]
    
    search_fields = [
        'registration__registration_number',
        'registration__full_name',
        'original_filename',
    ]
    
    readonly_fields = [
        'registration',
        'original_filename',
        'file_size',
        'mime_type',
        'uploaded_at',
    ]
    
    fields = [
        'registration',
        'document_type',
        'file',
        'original_filename',
        'file_size',
        'mime_type',
        'is_verified',
        'verified_by',
        'verification_notes',
        'uploaded_at',
    ]
    
    def registration_link(self, obj):
        """Link ke registration"""
        url = reverse('admin:registration_studentregistration_change', args=[obj.registration.id])
        return format_html('<a href="{}">{}</a>', url, obj.registration.registration_number)
    registration_link.short_description = 'Registration'
    
    def file_size_display(self, obj):
        """Display file size dalam KB/MB"""
        size = obj.file_size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = 'File Size'