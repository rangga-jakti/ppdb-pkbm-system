# apps/payments/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import uuid

class Payment(models.Model):
    """
    Transaksi pembayaran PPDB.
    CRITICAL: Status hanya boleh diubah via webhook yang terverifikasi.
    """
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', _('Menunggu Pembayaran')
        PAID = 'PAID', _('Lunas')
        EXPIRED = 'EXPIRED', _('Kadaluarsa')
        FAILED = 'FAILED', _('Gagal')
        REFUNDED = 'REFUNDED', _('Dikembalikan')
    
    class PaymentMethod(models.TextChoices):
        VA_BCA = 'VA_BCA', _('Virtual Account BCA')
        VA_BNI = 'VA_BNI', _('Virtual Account BNI')
        VA_MANDIRI = 'VA_MANDIRI', _('Virtual Account Mandiri')
        VA_BRI = 'VA_BRI', _('Virtual Account BRI')
        VA_PERMATA = 'VA_PERMATA', _('Virtual Account Permata')
        
    # User NULLABLE untuk public payment
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,  # ← WAJIB
        blank=True,  # ← WAJIB
        related_name='payments',
        help_text='NULL untuk pembayaran public (tanpa login)'
    )
    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Keys
    registration = models.OneToOneField(
        'registration.StudentRegistration',
        on_delete=models.PROTECT,  # PROTECT: jangan hapus payment jika ada registration
        related_name='payment'
    )
   # SESUDAH (NULLABLE untuk public payment):
    user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='payments',
    help_text='NULL untuk pembayaran public (tanpa login)'
)
    
    # Payment Gateway Reference
    gateway_order_id = models.CharField(
        _('Order ID Gateway'),
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Order ID dari Midtrans/Xendit'
    )
    gateway_transaction_id = models.CharField(
        _('Transaction ID Gateway'),
        max_length=100,
        blank=True,
        db_index=True,
        help_text='Transaction ID dari payment gateway'
    )
    
    # Virtual Account Info
    va_number = models.CharField(
        _('Nomor Virtual Account'),
        max_length=50,
        blank=True,
        db_index=True
    )
    payment_method = models.CharField(
        _('Metode Pembayaran'),
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True
    )
    
    # Amount
    amount = models.DecimalField(
        _('Jumlah Pembayaran'),
        max_digits=10,
        decimal_places=2,
        help_text='Dalam Rupiah'
    )
    admin_fee = models.DecimalField(
        _('Biaya Admin'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_amount = models.DecimalField(
        _('Total yang Harus Dibayar'),
        max_digits=10,
        decimal_places=2
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(_('Waktu Pembayaran'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Batas Waktu Pembayaran'), null=True, blank=True)
    
    # Raw Gateway Response (for debugging)
    gateway_response = models.JSONField(
        _('Response Gateway'),
        blank=True,
        null=True,
        help_text='Raw response dari payment gateway'
    )
    
    class Meta:
        db_table = 'payments'
        verbose_name = _('Pembayaran')
        verbose_name_plural = _('Pembayaran')
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['gateway_order_id']),
            models.Index(fields=['va_number']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.gateway_order_id} - Rp {self.total_amount} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total
        if self.amount:
            self.total_amount = self.amount + self.admin_fee
        super().save(*args, **kwargs)


class PaymentLog(models.Model):
    """
    Audit trail untuk semua event pembayaran.
    PENTING: Jangan pernah hapus record ini (compliance & debugging).
    """
    
    class EventType(models.TextChoices):
        CREATED = 'CREATED', _('Payment Created')
        WEBHOOK_RECEIVED = 'WEBHOOK_RECEIVED', _('Webhook Received')
        STATUS_CHANGED = 'STATUS_CHANGED', _('Status Changed')
        ERROR = 'ERROR', _('Error Occurred')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='logs'
    )
    
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices
    )
    
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    
    # Webhook signature verification
    signature_valid = models.BooleanField(null=True, blank=True)
    
    # Raw data
    request_data = models.JSONField(
        _('Request Data'),
        blank=True,
        null=True,
        help_text='Raw webhook/API request'
    )
    response_data = models.JSONField(
        _('Response Data'),
        blank=True,
        null=True
    )
    
    # Error tracking
    error_message = models.TextField(_('Error Message'), blank=True)
    
    # IP & User Agent (security)
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'payment_logs'
        verbose_name = _('Payment Log')
        verbose_name_plural = _('Payment Logs')
        indexes = [
            models.Index(fields=['payment', 'created_at']),
            models.Index(fields=['event_type', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} - {self.payment.gateway_order_id} at {self.created_at}"