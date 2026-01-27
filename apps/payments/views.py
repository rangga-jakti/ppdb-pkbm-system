"""
Views untuk Payment (PKBM Version - PUBLIC).
"""
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.accounts.permissions import staff_required
from .models import Payment
from .services import PaymentService
from apps.registration.models import StudentRegistration
from django.utils import timezone

import logging
import json

logger = logging.getLogger('apps.payments')


class CreatePaymentView(View):
    """PUBLIC - Create payment"""
    
    template_name = 'payments/create.html'
    
    def post(self, request, registration_id):
        """Buat payment dan redirect ke instructions"""
        registration = get_object_or_404(StudentRegistration, pk=registration_id)
        
        try:
            # Create payment (ini akan generate registration number juga)
            payment = PaymentService.create_payment_public(registration=registration)
            
            # Refresh registration dari DB untuk dapat nomor yang baru di-generate
            registration.refresh_from_db()
            
            # Success message dengan nomor pendaftaran
            messages.success(
                request,
                f'Nomor Pendaftaran Anda: {registration.registration_number}. '
                f'Silakan simpan nomor ini untuk cek status.'
            )
            
            logger.info(f"Payment created: {payment.gateway_order_id} for {registration.registration_number}")
            
            # Redirect ke instructions
            return redirect('payments:instructions', pk=payment.id)
            
        except ValueError as e:
            logger.warning(f"ValueError: {str(e)}")
            messages.error(request, str(e))
            return redirect('registration:check_status')
            
        except Exception as e:
            logger.error(f"Payment creation failed", exc_info=True)
            messages.error(request, f'Gagal membuat pembayaran: {str(e)}')
            return redirect('registration:check_status')
        
    def get(self, request, registration_id):
        """Tampilkan konfirmasi pembayaran (GET)"""
        
        registration = get_object_or_404(StudentRegistration, pk=registration_id)
        
        logger.info(f"Payment confirm - RegNum: {registration.registration_number}, Status: {registration.status}")
        
        # Verify status
        if registration.status != StudentRegistration.RegistrationStatus.SUBMITTED:
            messages.error(
                request, 
                f'Status pendaftaran: {registration.get_status_display()}. Harus SUBMITTED untuk membayar.'
            )
            return redirect('registration:check_status')
        
        # Check existing payment
        try:
            existing_payment = registration.payment
            if existing_payment.status == Payment.PaymentStatus.PENDING:
                logger.info(f"Payment exists, redirect to instructions")
                return redirect('payments:instructions', pk=existing_payment.id)
            elif existing_payment.status == Payment.PaymentStatus.PAID:
                messages.success(request, 'Pembayaran sudah lunas.')
                return redirect('registration:check_status')
        except Payment.DoesNotExist:
            pass
        
        # Render confirmation page
        return render(request, self.template_name, {
            'registration': registration,
            'amount': settings.REGISTRATION_FEE,
        })
    
    def post(self, request, registration_id):
        """Buat payment dan redirect ke instructions (POST)"""
        
        registration = get_object_or_404(StudentRegistration, pk=registration_id)
        
        try:
            # Create payment
            from apps.payments.services import PaymentService
            
            payment = PaymentService.create_payment_public(registration=registration)
            
            # Refresh registration
            registration.refresh_from_db()
            
            messages.success(
                request,
                f'Nomor Pendaftaran: {registration.registration_number}. Silakan lanjutkan pembayaran.'
            )
            
            logger.info(f"Payment created: {payment.gateway_order_id}")
            
            # Redirect ke instructions
            return redirect('payments:instructions', pk=payment.id)
            
        except ValueError as e:
            logger.warning(f"ValueError: {str(e)}")
            messages.error(request, str(e))
            return redirect('registration:check_status')
            
        except Exception as e:
            logger.error(f"Payment creation failed", exc_info=True)
            messages.error(request, f'Gagal membuat pembayaran: {str(e)}')
            return redirect('registration:check_status')


class PaymentInstructionsView(View):
    """PUBLIC - Instruksi pembayaran"""
    
    template_name = 'payments/instructions.html'
    
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        
        return render(request, self.template_name, {
            'payment': payment,
            'registration': payment.registration,
        })


class PaymentStatusView(View):
    """PUBLIC - Status pembayaran"""
    
    template_name = 'payments/status.html'
    
    def get(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        
        return render(request, self.template_name, {
            'payment': payment,
            'registration': payment.registration,
        })


@csrf_exempt
@require_POST
def midtrans_webhook(request):
    """Webhook dari Midtrans"""
    
    try:
        notification = json.loads(request.body)
        
        signature_key = notification.get('signature_key', '')
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        
        payment = PaymentService.handle_payment_notification(
            notification_data=notification,
            signature_key=signature_key,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if payment:
            return JsonResponse({'status': 'success'}, status=200)
        else:
            return JsonResponse({'status': 'payment_not_found'}, status=200)
            
    except Exception as e:
        logger.error(f"Webhook processing error", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=200)


@login_required
@staff_required
def simulate_payment(request, pk):
    """
    TESTING ONLY - Simulate payment success.
    Hanya untuk staff/admin.
    """
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_paid':
            # Simulate payment success
            from django.db import transaction
            
            with transaction.atomic():
                payment.status = Payment.PaymentStatus.PAID
                payment.paid_at = timezone.now()
                payment.save()
                
                # Update registration status
                registration = payment.registration
                registration.status = StudentRegistration.RegistrationStatus.PAID
                registration.save()
                
                # Log
                from .models import PaymentLog
                PaymentLog.objects.create(
                    payment=payment,
                    event_type=PaymentLog.EventType.STATUS_CHANGED,
                    old_status=Payment.PaymentStatus.PENDING,
                    new_status=Payment.PaymentStatus.PAID,
                    request_data={'simulated': True, 'by': str(request.user)}
                )
                
                logger.info(
                    f"Payment SIMULATED as PAID: {payment.gateway_order_id} by {request.user}"
                )
                
                messages.success(
                    request, 
                    f'Payment {payment.gateway_order_id} marked as PAID (SIMULATED)'
                )
        
        return redirect('payments:simulate', pk=payment.id)
    
    return render(request, 'payments/simulate.html', {
        'payment': payment,
        'registration': payment.registration,
    })