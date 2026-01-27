
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.payments.models import Payment
from apps.registration.models import StudentRegistration
import logging

logger = logging.getLogger('apps.payments')


class Command(BaseCommand):
    help = 'Expire pending payments that are past their expiry date'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be expired without actually expiring'
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Find expired payments
        expired_payments = Payment.objects.filter(
            status=Payment.PaymentStatus.PENDING,
            expires_at__lt=now
        )
        
        count = expired_payments.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would expire {count} payments'
                )
            )
            
            for payment in expired_payments[:10]:
                reg = payment.registration
                self.stdout.write(
                    f'  - {reg.registration_number} ({reg.full_name}) '
                    f'Expired: {payment.expires_at}'
                )
            
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        
        else:
            # Update status to EXPIRED
            updated = expired_payments.update(
                status=Payment.PaymentStatus.EXPIRED
            )
            
            # OPTIONAL: Update registration status juga
            registration_ids = expired_payments.values_list('registration_id', flat=True)
            StudentRegistration.objects.filter(
                id__in=registration_ids,
                status=StudentRegistration.RegistrationStatus.SUBMITTED
            ).update(
                status=StudentRegistration.RegistrationStatus.DRAFT  # Atau buat status EXPIRED baru
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully expired {updated} payments'
                )
            )
            
            logger.info(f'Expired {updated} payments via management command')