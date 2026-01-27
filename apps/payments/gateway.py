"""
Midtrans Payment Gateway Client.
Handle semua komunikasi dengan Midtrans API.

CRITICAL SECURITY NOTES:
1. SERVER_KEY tidak boleh exposed ke frontend
2. Semua request harus dari backend
3. Signature verification WAJIB di webhook
"""
import midtransclient
from django.conf import settings
from typing import Dict, Any
import logging
import requests
import base64
import hashlib
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MidtransClient:
    """
    Wrapper untuk Midtrans API client.
    Singleton pattern untuk reuse connection.
    """
    
    _snap_client = None
    _core_client = None
    
    @classmethod
    def get_snap_client(cls):
        """Get atau create Snap API client (untuk VA transactions)"""
        if cls._snap_client is None:
            cls._snap_client = midtransclient.Snap(
                is_production=settings.MIDTRANS_CONFIG['IS_PRODUCTION'],
                server_key=settings.MIDTRANS_CONFIG['SERVER_KEY'],
                client_key=settings.MIDTRANS_CONFIG['CLIENT_KEY']
            )
        return cls._snap_client
    
    @classmethod
    def get_core_client(cls):
        """Get atau create Core API client (untuk status check)"""
        if cls._core_client is None:
            cls._core_client = midtransclient.CoreApi(
                is_production=settings.MIDTRANS_CONFIG['IS_PRODUCTION'],
                server_key=settings.MIDTRANS_CONFIG['SERVER_KEY'],
                client_key=settings.MIDTRANS_CONFIG['CLIENT_KEY']
            )
        return cls._core_client
    
    @classmethod
    def create_va_transaction(
        cls,
        order_id: str,
        gross_amount: int,
        customer_details: Dict[str, Any],
        item_details: list,
        enabled_payments: list = None
    ) -> Dict[str, Any]:
        """
        Create Virtual Account transaction via Snap API.
        
        Args:
            order_id: Unique order ID (dari Payment model)
            gross_amount: Total amount dalam Rupiah (integer)
            customer_details: Data customer (email, name, phone)
            item_details: List items yang dibayar
            enabled_payments: List payment methods yang diaktifkan
        
        Returns:
            Dict response dari Midtrans
        
        Raises:
            Exception jika gagal create transaction
        """
        if enabled_payments is None:
            enabled_payments = [
                'bca_va', 'bni_va', 'bri_va', 'permata_va', 'other_va'
            ]
        
        # Calculate expiry time
        from datetime import datetime, timedelta
        expiry = datetime.now() + timedelta(hours=settings.PAYMENT_EXPIRY_HOURS)
        
        transaction_params = {
            'transaction_details': {
                'order_id': order_id,
                'gross_amount': gross_amount,
            },
            'customer_details': customer_details,
            'item_details': item_details,
            'enabled_payments': enabled_payments,
            'expiry': {
                'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S +0700'),
                'unit': 'hours',
                'duration': settings.PAYMENT_EXPIRY_HOURS,
            },
            # Custom field untuk tracking
            'custom_field1': order_id,
            'custom_field2': customer_details.get('email', ''),
        }
        
        try:
            snap = cls.get_snap_client()
            response = snap.create_transaction(transaction_params)
            
            logger.info(
                f"Midtrans transaction created: {order_id}",
                extra={'response': response}
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Failed to create Midtrans transaction: {order_id}",
                exc_info=True,
                extra={'error': str(e)}
            )
            raise
    
    @classmethod
    def get_transaction_status(cls, order_id: str) -> Dict[str, Any]:
        """
        Check transaction status dari Midtrans.
        Digunakan untuk manual verification jika webhook gagal.
        
        Args:
            order_id: Order ID yang di-check
        
        Returns:
            Dict status dari Midtrans
        """
        try:
            core = cls.get_core_client()
            response = core.transactions.status(order_id)
            
            logger.info(
                f"Midtrans status checked: {order_id}",
                extra={'status': response.get('transaction_status')}
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Failed to check Midtrans status: {order_id}",
                exc_info=True
            )
            raise
    
    @classmethod
    def verify_signature(
        cls,
        order_id: str,
        status_code: str,
        gross_amount: str,
        signature_key: str
    ) -> bool:
        """
        Verify signature dari webhook notification.
        
        CRITICAL: Ini adalah security layer utama webhook.
        Tanpa ini, attacker bisa fake notification.
        
        Args:
            order_id: Order ID dari webhook
            status_code: Status code dari webhook
            gross_amount: Amount dari webhook
            signature_key: Signature yang dikirim Midtrans
        
        Returns:
            True jika signature valid, False otherwise
        """
        import hashlib
        
        server_key = settings.MIDTRANS_CONFIG['SERVER_KEY']
        
        # SHA512(order_id + status_code + gross_amount + server_key)
        signature_string = f"{order_id}{status_code}{gross_amount}{server_key}"
        calculated_signature = hashlib.sha512(
            signature_string.encode('utf-8')
        ).hexdigest()
        
        is_valid = calculated_signature == signature_key
        
        if not is_valid:
            logger.warning(
                f"Invalid signature for order: {order_id}",
                extra={
                    'expected': calculated_signature,
                    'received': signature_key
                }
            )
        
        return is_valid
    
    @staticmethod
    def _get_headers():
        """Get authorization headers"""
        server_key = settings.MIDTRANS_SERVER_KEY
        
        # Encode server key untuk Basic Auth
        auth_string = f"{server_key}:"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_string = base64_bytes.decode('ascii')
        
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Basic {base64_string}'
        }
    
    @staticmethod
    def create_va_transaction(order_id, gross_amount, customer_details, item_details):
        """
        Create Virtual Account transaction
        
        Returns:
            dict: Response dari Midtrans dengan VA number
        """
        
        url = f"{settings.MIDTRANS_API_URL}/charge"
        
        payload = {
            "payment_type": "bank_transfer",
            "transaction_details": {
                "order_id": order_id,
                "gross_amount": gross_amount
            },
            "customer_details": customer_details,
            "item_details": item_details,
            "bank_transfer": {
                "bank": "bca"  # Bisa ganti: bni, bri, permata
            }
        }
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=MidtransClient._get_headers(),
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Midtrans VA created: {order_id}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Midtrans API error: {str(e)}", exc_info=True)
            raise Exception(f"Gagal membuat VA: {str(e)}")
    
    @staticmethod
    def verify_signature(order_id, status_code, gross_amount, signature_key):
        """
        Verify Midtrans webhook signature
        
        CRITICAL SECURITY: WAJIB verify setiap webhook!
        """
        server_key = settings.MIDTRANS_SERVER_KEY
        
        # Signature = SHA512(order_id + status_code + gross_amount + server_key)
        signature_string = f"{order_id}{status_code}{gross_amount}{server_key}"
        
        hash_object = hashlib.sha512(signature_string.encode())
        calculated_signature = hash_object.hexdigest()
        
        is_valid = calculated_signature == signature_key
        
        if not is_valid:
            logger.warning(
                f"Invalid signature for order: {order_id}",
                extra={
                    'calculated': calculated_signature,
                    'received': signature_key
                }
            )
        
        return is_valid