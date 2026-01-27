"""
Webhook handler untuk payment notification dari Midtrans.

CRITICAL SECURITY NOTES:
1. Endpoint ini PUBLIC (tidak pakai @login_required)
2. WAJIB verify signature untuk setiap request
3. Idempotent (bisa dipanggil berkali-kali)
4. Logging semua request (audit trail)

PRODUCTION CHECKLIST:
- [ ] SSL/TLS enabled (HTTPS)
- [ ] Firewall rules (hanya allow IP Midtrans)
- [ ] Rate limiting
- [ ] Monitoring & alerting
"""
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
import json
import logging

from .services import PaymentService

logger = logging.getLogger('apps.payments')


@csrf_exempt
@require_POST
def midtrans_webhook(request):
    """
    Webhook endpoint untuk Midtrans payment notification.
    
    URL: /payments/webhook/midtrans/
    Method: POST
    Content-Type: application/json
    
    Midtrans akan POST ke endpoint ini ketika:
    - Payment berhasil (settlement)
    - Payment pending
    - Payment expired
    - Payment cancelled
    
    IMPORTANT: 
    - Midtrans bisa mengirim notification berkali-kali untuk satu transaksi
    - Kita harus handle idempotency (hasil sama meski dipanggil berkali-kali)
    """
    
    # Get IP address (untuk logging & security)
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    logger.info(
        f"Webhook received from IP: {ip_address}",
        extra={'user_agent': user_agent}
    )
    
    # Parse request body
    try:
        notification = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook request", extra={'ip': ip_address})
        return HttpResponseBadRequest("Invalid JSON")
    
    # Log raw notification (untuk debugging)
    logger.debug(
        "Webhook notification received",
        extra={'notification': notification}
    )
    
    # Extract required fields
    order_id = notification.get('order_id')
    signature_key = notification.get('signature_key')
    
    if not order_id or not signature_key:
        logger.error(
            "Missing required fields in webhook",
            extra={'notification': notification}
        )
        return HttpResponseBadRequest("Missing required fields")
    
    # Process notification via service layer
    try:
        payment = PaymentService.handle_payment_notification(
            notification_data=notification,
            signature_key=signature_key,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if payment is None:
            # Signature invalid atau payment tidak ditemukan
            logger.error(
                f"Failed to process notification for order: {order_id}",
                extra={'notification': notification}
            )
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to process notification'
            }, status=400)
        
        # Success response
        logger.info(
            f"Webhook processed successfully for order: {order_id}",
            extra={
                'payment_id': str(payment.id),
                'new_status': payment.status
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Notification processed successfully'
        })
        
    except Exception as e:
        logger.error(
            f"Unexpected error processing webhook for order: {order_id}",
            exc_info=True,
            extra={'notification': notification}
        )
        
        # Return 200 anyway (agar Midtrans tidak retry terus-menerus)
        # Tapi log error untuk investigation
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


def get_client_ip(request):
    """
    Get client IP address dari request.
    Handle proxy headers (X-Forwarded-For).
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================================
# WEBHOOK SECURITY ENHANCEMENTS (PRODUCTION)
# ============================================================================

def verify_midtrans_ip(request):
    """
    Verify bahwa request datang dari IP Midtrans.
    
    Midtrans IP Ranges (per 2024):
    - Production: 103.208.23.0/24, 103.208.23.6, 103.208.23.7
    - Sandbox: Various
    
    IMPORTANT: Update IP list sesuai dokumentasi Midtrans terbaru.
    """
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Midtrans IP whitelist (update sesuai dokumentasi)
    allowed_ips = settings.MIDTRANS_WEBHOOK_IPS if hasattr(settings, 'MIDTRANS_WEBHOOK_IPS') else []
    
    if settings.MIDTRANS_CONFIG['IS_PRODUCTION'] and allowed_ips:
        if client_ip not in allowed_ips:
            logger.warning(
                f"Webhook request from unauthorized IP: {client_ip}"
            )
            return False
    
    return True


# Decorator untuk IP verification (optional, untuk production)
def require_midtrans_ip(view_func):
    """Decorator untuk verify IP Midtrans"""
    def wrapped_view(request, *args, **kwargs):
        if not verify_midtrans_ip(request):
            return JsonResponse({
                'status': 'error',
                'message': 'Unauthorized IP'
            }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapped_view