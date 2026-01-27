
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from typing import Dict, Any, Optional
import logging

from .models import Payment, PaymentLog
from .gateway import MidtransClient
from apps.registration.models import StudentRegistration

logger = logging.getLogger('apps.payments')


class PaymentService:
    """Service untuk handle payment operations"""
    
    @staticmethod
    @transaction.atomic
    def create_payment_public(registration: StudentRegistration) -> Payment:
        """
        Create payment PUBLIC (tanpa user).
        NO EXPIRY - VA tetap aktif sampai dibayar.
        """
        
        # Check existing payment
        if hasattr(registration, 'payment'):
            existing_payment = registration.payment
            if existing_payment.status in [Payment.PaymentStatus.PENDING, Payment.PaymentStatus.PAID]:
                logger.info(f"Returning existing payment: {existing_payment.gateway_order_id}")
                return existing_payment
        
        if registration.status != StudentRegistration.RegistrationStatus.SUBMITTED:
            raise ValueError('Pendaftaran harus dalam status SUBMITTED.')
        
        # Verify registration number exists
        if not registration.registration_number:
            raise ValueError(
                'Registration number tidak ditemukan. '
                'Hubungi admin atau coba submit ulang.'
            )
        
        # Calculate amount
        amount = Decimal(str(settings.REGISTRATION_FEE))
        admin_fee = Decimal('0.00')
        
        # Generate order ID
        order_id = PaymentService._generate_order_id(registration)
        
        # Create Payment object
        payment = Payment.objects.create(
            registration=registration,
            user=None,
            gateway_order_id=order_id,
            amount=amount,
            admin_fee=admin_fee,
            status=Payment.PaymentStatus.PENDING,
            payment_method=Payment.PaymentMethod.VA_BCA,
            expires_at=None  # NO EXPIRY
        )
        
        # Log creation
        PaymentLog.objects.create(
            payment=payment,
            event_type=PaymentLog.EventType.CREATED,
            new_status=Payment.PaymentStatus.PENDING,
            request_data={'registration_id': str(registration.id), 'amount': str(amount)}
        )
        
        # TRY Midtrans, FALLBACK to dummy VA
        try:
            midtrans_response = PaymentService._create_midtrans_transaction(payment, registration)
            
            payment.gateway_response = midtrans_response
            va_numbers = midtrans_response.get('va_numbers', [])
            if va_numbers:
                payment.va_number = va_numbers[0].get('va_number', '')
            
            logger.info(f"Payment created with Midtrans: {order_id}")
            
        except Exception as e:
            # FALLBACK: Create dummy VA for TESTING
            logger.warning(f"Midtrans failed, using dummy VA: {str(e)}")
            
            import random
            payment.va_number = f"8808{random.randint(100000000000, 999999999999)}"
            payment.gateway_response = {
                'mode': 'TESTING_MODE',
                'error': str(e),
                'note': 'Dummy VA - Untuk testing tanpa Midtrans'
            }
        
        # Save payment (no expiry set)
        payment.save()
        
        logger.info(f"Payment created (no expiry): {order_id} (VA: {payment.va_number})")
        return payment
    
    @staticmethod
    def _generate_order_id(registration: StudentRegistration) -> str:
        """
        Generate unique order ID untuk Midtrans.
        Format: PPDB-2026-XXXX-TIMESTAMP
        """
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        reg_number = registration.registration_number.replace('PPDB-', '')
        return f"PPDB-{reg_number}-{timestamp}"
    
    @staticmethod
    def _create_midtrans_transaction(
        payment: Payment,
        registration: StudentRegistration
    ) -> Dict[str, Any]:
        """Create transaction di Midtrans via Snap API"""
        
        customer_details = {
            'first_name': registration.full_name,
            'email': registration.contact_email if registration.contact_email != '-' else 'noemail@ppdb.com',
            'phone': registration.contact_phone,
        }
        
        item_details = [
            {
                'id': 'PPDB_FEE',
                'price': int(payment.amount),
                'quantity': 1,
                'name': f'Biaya Pendaftaran PPDB {registration.academic_year}',
            }
        ]
        
        if payment.admin_fee > 0:
            item_details.append({
                'id': 'ADMIN_FEE',
                'price': int(payment.admin_fee),
                'quantity': 1,
                'name': 'Biaya Administrasi',
            })
        
        return MidtransClient.create_va_transaction(
            order_id=payment.gateway_order_id,
            gross_amount=int(payment.total_amount),
            customer_details=customer_details,
            item_details=item_details,
        )
    
    @staticmethod
    @transaction.atomic
    def handle_payment_notification(
        notification_data: Dict[str, Any],
        signature_key: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[Payment]:
        """
        Handle webhook notification dari Midtrans.
        
        CRITICAL SECURITY:
        1. Verify signature WAJIB
        2. Idempotent
        3. Atomic transaction
        """
        order_id = notification_data.get('order_id')
        transaction_status = notification_data.get('transaction_status')
        fraud_status = notification_data.get('fraud_status')
        status_code = notification_data.get('status_code')
        gross_amount = notification_data.get('gross_amount')
        
        # Get payment
        try:
            payment = Payment.objects.select_for_update().get(
                gateway_order_id=order_id
            )
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for order: {order_id}")
            return None
        
        # Verify signature
        is_signature_valid = MidtransClient.verify_signature(
            order_id=order_id,
            status_code=status_code,
            gross_amount=gross_amount,
            signature_key=signature_key
        )
        
        # Log webhook received
        webhook_log = PaymentLog.objects.create(
            payment=payment,
            event_type=PaymentLog.EventType.WEBHOOK_RECEIVED,
            signature_valid=is_signature_valid,
            request_data=notification_data,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        if not is_signature_valid:
            logger.error(
                f"Invalid signature for webhook: {order_id}",
                extra={'log_id': str(webhook_log.id)}
            )
            return None
        
        # Process based on transaction_status
        old_status = payment.status
        new_status = PaymentService._map_midtrans_status(
            transaction_status, fraud_status
        )
        
        # Idempotency check
        if payment.status in [Payment.PaymentStatus.PAID, Payment.PaymentStatus.REFUNDED]:
            logger.info(
                f"Payment already in final status: {order_id}",
                extra={'status': payment.status}
            )
            return payment
        
        # Update payment status
        payment.status = new_status
        payment.gateway_transaction_id = notification_data.get('transaction_id', '')
        payment.payment_method = PaymentService._map_payment_method(
            notification_data.get('payment_type')
        )
        payment.va_number = notification_data.get('va_numbers', [{}])[0].get('va_number', '')
        
        if new_status == Payment.PaymentStatus.PAID:
            payment.paid_at = timezone.now()
        
        payment.save()
        
        # Log status change
        PaymentLog.objects.create(
            payment=payment,
            event_type=PaymentLog.EventType.STATUS_CHANGED,
            old_status=old_status,
            new_status=new_status,
            request_data=notification_data,
        )
        
        # Update registration status jika payment PAID
        if new_status == Payment.PaymentStatus.PAID:
            registration = payment.registration
            registration.status = StudentRegistration.RegistrationStatus.PAID
            registration.save()
            
            logger.info(
                f"Registration updated to PAID: {registration.registration_number}",
                extra={'payment_id': str(payment.id)}
            )
        
        return payment
    
    @staticmethod
    def _map_midtrans_status(
        transaction_status: str,
        fraud_status: str = None
    ) -> str:
        """Map Midtrans status ke Payment status"""
        
        if transaction_status == 'capture':
            if fraud_status == 'accept':
                return Payment.PaymentStatus.PAID
            return Payment.PaymentStatus.PENDING
        
        elif transaction_status == 'settlement':
            return Payment.PaymentStatus.PAID
        
        elif transaction_status in ['cancel', 'deny']:
            return Payment.PaymentStatus.FAILED
        
        elif transaction_status == 'expire':
            return Payment.PaymentStatus.EXPIRED
        
        elif transaction_status == 'pending':
            return Payment.PaymentStatus.PENDING
        
        elif transaction_status == 'refund':
            return Payment.PaymentStatus.REFUNDED
        
        return Payment.PaymentStatus.PENDING
    
    @staticmethod
    def _map_payment_method(payment_type: str) -> str:
        """Map Midtrans payment_type ke Payment.PaymentMethod"""
        mapping = {
            'bank_transfer': Payment.PaymentMethod.VA_BCA,
            'bca_va': Payment.PaymentMethod.VA_BCA,
            'bni_va': Payment.PaymentMethod.VA_BNI,
            'bri_va': Payment.PaymentMethod.VA_BRI,
            'permata_va': Payment.PaymentMethod.VA_PERMATA,
            'echannel': Payment.PaymentMethod.VA_MANDIRI,
        }
        return mapping.get(payment_type, Payment.PaymentMethod.VA_BCA)
