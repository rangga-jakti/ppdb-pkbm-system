"""
Models untuk Registration (PPDB PKBM CIPTA TUNAS KARYA - Public Version).
Siswa tidak perlu akun, pendaftaran langsung public.
"""
from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
import uuid


class StudentRegistration(models.Model):
    """
    Data pendaftaran siswa PKBM.
    TIDAK WAJIB memiliki user account (public registration).
    """
    
    class RegistrationStatus(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft - Belum Submit')
        SUBMITTED = 'SUBMITTED', _('Submitted - Menunggu Pembayaran')
        PAYMENT_EXPIRED = 'PAYMENT_EXPIRED', _('Payment Expired - Daftar Ulang') 
        PAID = 'PAID', _('Paid - Menunggu Verifikasi')
        VERIFIED = 'VERIFIED', _('Verified - Diterima')
        REJECTED = 'REJECTED', _('Rejected - Tidak Lolos Verifikasi')
    
    class ProgramChoice(models.TextChoices):
        PAKET_A = 'PAKET_A', _('Paket A (Setara SD)')
        PAKET_B = 'PAKET_B', _('Paket B (Setara SMP)')
        PAKET_C = 'PAKET_C', _('Paket C (Setara SMA)')  
        
    class ReligionChoices(models.TextChoices):
        ISLAM = 'ISLAM', 'Islam'
        KRISTEN = 'KRISTEN', 'Kristen'
        KATOLIK = 'KATOLIK', 'Katolik'
        HINDU = 'HINDU', 'Hindu'
        BUDDHA = 'BUDDHA', 'Buddha'
        KONGHUCU = 'KONGHUCU', 'Konghucu'
        
    # Declaration (Pernyataan)
    declaration_agreed = models.BooleanField(
        _('Persetujuan Pernyataan'),
        default=False,
        help_text='Centang jika menyetujui pernyataan'
    )
    declaration_agreed_at = models.DateTimeField(
        _('Waktu Persetujuan'),
        null=True,
        blank=True
    )

    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign Keys (NULLABLE - siswa tidak wajib punya akun)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registrations',
        help_text='Opsional - hanya untuk admin yang input manual'
    )
    
    # Metadata
    registration_number = models.CharField(
        _('Nomor Pendaftaran'),
        max_length=20,
        db_index=True,
        editable=False
    )
    academic_year = models.CharField(
        _('Tahun Ajaran'),
        max_length=9,
        help_text='Format: 2024/2025'
    )
    status = models.CharField(
        max_length=20,
        choices=RegistrationStatus.choices,
        default=RegistrationStatus.DRAFT,
        db_index=True
    )
    
    # Data Pribadi Siswa
    full_name = models.CharField(_('Nama Lengkap'), max_length=255)

    nik = models.CharField(
        _('NIK'),
        max_length=16,
        validators=[RegexValidator(r'^\d{16}$', 'NIK harus 16 digit angka')],
        help_text='Nomor Induk Kependudukan (16 digit)',
        blank=True,
        null=True,
    )

    nisn = models.CharField(
        _('NISN'),
        max_length=10,
        blank=True,
        validators=[RegexValidator(r'^\d{10}$', 'NISN harus 10 digit angka')],
        help_text='Nomor Induk Siswa Nasional (10 digit)'
    )
    
    nisn = models.CharField(
    _('NISN'),
    max_length=10,
    blank=True,
    validators=[RegexValidator(r'^\d{10}$', 'NISN harus 10 digit angka')],
    help_text='Nomor Induk Siswa Nasional (10 digit)'
    )
    birth_place = models.CharField(_('Tempat Lahir'), max_length=100)
    birth_date = models.DateField(_('Tanggal Lahir'))
    gender = models.CharField(
        _('Jenis Kelamin'),
        max_length=1,
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')]
    )
    
    # Kontak Siswa (WAJIB untuk tracking tanpa akun)
    contact_email = models.EmailField(
        _('Email Kontak'),
        max_length=255,
        help_text='Email untuk notifikasi status pendaftaran'
    )
    contact_phone = models.CharField(
        _('No. HP Kontak'),
        max_length=20,
        help_text='Nomor HP yang bisa dihubungi'
    )
    
    religion = models.CharField(
    _('Agama'),
    max_length=20,
    choices=ReligionChoices.choices,
    blank=True,
    null=True
    )

    
    # Data Asal Sekolah
    previous_school = models.CharField(_('Asal Sekolah'), max_length=255)
    previous_school_npsn = models.CharField(
        _('NPSN Sekolah Asal'),
        max_length=8,
        blank=True
    )
    graduation_year = models.PositiveSmallIntegerField(_('Tahun Lulus'))
    
    # Program Pilihan
    program_choice = models.CharField(
        _('Pilihan Program'),
        max_length=20,
        choices=ProgramChoice.choices
    )
    
    # Alamat
    address = models.TextField(_('Alamat Lengkap'))
    city = models.CharField(_('Kota/Kabupaten'), max_length=100)
    province = models.CharField(_('Provinsi'), max_length=100)
    postal_code = models.CharField(_('Kode Pos'), max_length=5, blank=True)
    
    # Kontak Darurat (Orang Tua/Wali)
    father_name = models.CharField(_('Nama Ayah'), max_length=255, blank=True, null=True)
    father_occupation = models.CharField(_('Pekerjaan Ayah'), max_length=255, blank=True, null=True)

    mother_name = models.CharField(_('Nama Ibu'), max_length=255, blank=True, null=True)
    mother_occupation = models.CharField(_('Pekerjaan Ibu'), max_length=255, blank=True, null=True)    
    
    parent_phone = models.CharField(_('No. HP Orang Tua'), max_length=20)
    
    # Timestamp & Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(_('Waktu Submit'), null=True, blank=True)
    verified_at = models.DateTimeField(_('Waktu Verifikasi'), null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_registrations'
    )
    
    # Notes dari panitia
    verification_notes = models.TextField(_('Catatan Verifikasi'), blank=True)
    
    class Meta:
        db_table = 'student_registrations'
        verbose_name = _('Pendaftaran Siswa')
        verbose_name_plural = _('Pendaftaran Siswa')
        indexes = [
            models.Index(fields=['status', 'academic_year']),
            models.Index(fields=['registration_number']),
            models.Index(fields=['nisn']),
            models.Index(fields=['contact_email']),
            models.Index(fields=['contact_phone']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.registration_number} - {self.full_name}"

class Document(models.Model):
    """
    Dokumen yang di-upload siswa.
    SEMUA WAJIB: KTP, KK, Akta
    """
    
    class DocumentType(models.TextChoices):
        KTP = 'KTP', _('KTP Siswa/Orang Tua')
        KK = 'KK', _('Kartu Keluarga')
        AKTA = 'AKTA', _('Akta Kelahiran')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.ForeignKey(
        StudentRegistration,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    
    document_type = models.CharField(
        _('Jenis Dokumen'),
        max_length=20,
        choices=DocumentType.choices
    )
    file = models.FileField(
        _('File'),
        upload_to='documents/%Y/%m/',
        max_length=500
    )
    original_filename = models.CharField(_('Nama File Asli'), max_length=255)
    file_size = models.PositiveIntegerField(_('Ukuran File (bytes)'))
    mime_type = models.CharField(_('MIME Type'), max_length=100)
    
    # Verifikasi dokumen
    is_verified = models.BooleanField(_('Sudah Diverifikasi'), default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    verification_notes = models.TextField(_('Catatan Verifikasi'), blank=True)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'documents'
        verbose_name = _('Dokumen')
        verbose_name_plural = _('Dokumen')
        unique_together = [['registration', 'document_type']]
        indexes = [
            models.Index(fields=['registration', 'document_type']),
        ]
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.registration.full_name}"