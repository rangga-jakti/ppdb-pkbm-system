"""
Custom validators untuk registration & document upload.
"""
import magic
from django.core.exceptions import ValidationError
from django.conf import settings
import os


def validate_file_size(file):
    """
    Validate ukuran file upload.
    Maximum size dari settings.MAX_UPLOAD_SIZE
    """
    if file.size > settings.MAX_UPLOAD_SIZE:
        max_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ValidationError(
            f'Ukuran file terlalu besar. Maksimal {max_mb:.1f} MB.'
        )


def validate_file_extension(file):
    """
    Validate extension file.
    Allowed extensions dari settings.ALLOWED_DOCUMENT_TYPES
    """
    ext = os.path.splitext(file.name)[1][1:].lower()
    
    if ext not in settings.ALLOWED_DOCUMENT_TYPES:
        allowed = ', '.join(settings.ALLOWED_DOCUMENT_TYPES)
        raise ValidationError(
            f'Format file tidak didukung. Format yang diperbolehkan: {allowed}'
        )


def validate_file_content(file):
    """
    Validate actual file content (bukan hanya extension).
    Ini mencegah user rename .exe jadi .pdf
    
    CRITICAL SECURITY: Gunakan python-magic untuk detect real MIME type
    """
    # Read first chunk untuk detect MIME type
    file.seek(0)
    file_content = file.read(2048)
    file.seek(0)
    
    mime = magic.from_buffer(file_content, mime=True)
    
    # Allowed MIME types
    allowed_mimes = {
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/jpg',
    }
    
    if mime not in allowed_mimes:
        raise ValidationError(
            f'Tipe file tidak valid. Detected: {mime}'
        )


def validate_nisn(value):
    """
    Validate NISN (Nomor Induk Siswa Nasional).
    NISN harus 10 digit angka.
    """
    if not value.isdigit():
        raise ValidationError('NISN harus berupa angka.')
    
    if len(value) != 10:
        raise ValidationError('NISN harus 10 digit.')


def validate_graduation_year(value):
    """
    Validate tahun lulus.
    Tidak boleh lebih dari tahun sekarang + 1
    """
    from datetime import datetime
    current_year = datetime.now().year
    
    if value > current_year + 1:
        raise ValidationError(
            f'Tahun lulus tidak valid. Maksimal {current_year + 1}.'
        )
    
    if value < 2000:
        raise ValidationError('Tahun lulus terlalu lama.')