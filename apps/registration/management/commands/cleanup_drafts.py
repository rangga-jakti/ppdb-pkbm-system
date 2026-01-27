
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.registration.models import StudentRegistration
import logging

logger = logging.getLogger('apps.registration')


class Command(BaseCommand):
    help = 'Delete draft registrations older than 3 days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Number of days to keep drafts (default: 3)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Find old drafts
        old_drafts = StudentRegistration.objects.filter(
            status=StudentRegistration.RegistrationStatus.DRAFT,
            created_at__lt=cutoff_date
        )
        
        count = old_drafts.count()
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} draft registrations older than {days} days'
                )
            )
            
            for draft in old_drafts[:10]:  # Show first 10
                self.stdout.write(f'  - {draft.full_name} (Created: {draft.created_at})')
            
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')
        
        else:
            # Delete old drafts
            deleted_data = []
            for draft in old_drafts:
                deleted_data.append({
                    'name': draft.full_name,
                    'created': draft.created_at,
                })
            
            old_drafts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} draft registrations older than {days} days'
                )
            )
            
            logger.info(
                f'Cleanup: Deleted {count} drafts older than {days} days',
                extra={'deleted': deleted_data}
            )