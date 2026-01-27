
from django.db import transaction
from django.utils import timezone
import logging

from .models import StudentRegistration

logger = logging.getLogger('apps.registration')


class RegistrationService:
    """Service untuk registration logic"""
    
    @staticmethod
    @transaction.atomic
    def submit_registration(registration: StudentRegistration) -> StudentRegistration:
        """
        Submit registration dan GENERATE NOMOR PENDAFTARAN.
        
        CRITICAL: Nomor di-generate DI SINI saat submit.
        """
        
        logger.info(f"=== SUBMIT START === ID: {registration.id}, Name: {registration.full_name}")
        
        # Check status
        if registration.status != StudentRegistration.RegistrationStatus.DRAFT:
            logger.error(f"Status not DRAFT: {registration.status}")
            raise ValueError('Pendaftaran sudah pernah disubmit.')
        
        # ========================================
        # GENERATE REGISTRATION NUMBER
        # ========================================
        if not registration.registration_number:
            logger.info("Generating registration number...")
            
            try:
                # Extract year dari academic_year (e.g., "2025/2026" → 2026)
                if registration.academic_year:
                    year = int(registration.academic_year.split('/')[1])
                    logger.info(f"Year from academic_year: {year}")
                else:
                    year = timezone.now().year + 1
                    logger.info(f"Year from current: {year}")
                
                # Get last registration number for this year
                last_reg = StudentRegistration.objects.filter(
                    registration_number__startswith=f'PPDB-{year}',
                    registration_number__isnull=False
                ).exclude(
                    registration_number=''
                ).order_by('-registration_number').first()
                
                if last_reg:
                    logger.info(f"Last registration: {last_reg.registration_number}")
                    last_num = int(last_reg.registration_number.split('-')[-1])
                    new_num = last_num + 1
                else:
                    logger.info("No previous registration, starting from 1")
                    new_num = 1
                
                # Generate new number
                new_registration_number = f'PPDB-{year}-{new_num:05d}'
                logger.info(f"NEW NUMBER: {new_registration_number}")
                
                # SET IT
                registration.registration_number = new_registration_number
                
            except Exception as e:
                logger.error(f"Generation error: {str(e)}", exc_info=True)
                raise ValueError(f'Gagal generate nomor: {str(e)}')
        else:
            logger.info(f"Number already exists: {registration.registration_number}")
        
        # Update status
        registration.status = StudentRegistration.RegistrationStatus.SUBMITTED
        registration.submitted_at = timezone.now()
        
        # SAVE
        logger.info(f"Saving... Number: {registration.registration_number}")
        registration.save()
        
        # Verify after save
        registration.refresh_from_db()
        logger.info(f"After refresh: {registration.registration_number}")
        
        if not registration.registration_number:
            logger.error("CRITICAL: Number is EMPTY after save!")
            raise ValueError('Nomor tidak tersimpan. Hubungi admin.')
        
        logger.info(f"=== SUBMIT SUCCESS === {registration.registration_number}")
        
        return registration