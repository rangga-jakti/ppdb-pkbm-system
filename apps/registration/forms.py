"""
Forms untuk pendaftaran siswa & upload dokumen.
PUBLIC FORM - tidak memerlukan login.
"""
from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML

from .models import StudentRegistration, Document
from .validators import (
    validate_file_size,
    validate_file_extension,
    validate_file_content,
    validate_nisn,
    validate_graduation_year,
)


class StudentRegistrationForm(forms.ModelForm):
    """
    Form pendaftaran siswa PKBM - PUBLIC (tanpa login).
    Contact email & phone WAJIB untuk tracking tanpa akun.
    """
    
    class Meta:
        model = StudentRegistration
        fields = [
            # Data Pribadi
            'full_name',
            'nik',
            'nisn',
            'birth_place',
            'birth_date',
            'gender',
            'religion',
            
            # Sekolah
            'previous_school',
            'previous_school_npsn',
            'graduation_year',
            'program_choice',
            
             # Kontak
            'contact_email',
            'contact_phone',
            
             # Alamat
            'address',
            'city',
            'province',
            'postal_code',
                
            # Kontak (WAJIB untuk tracking)
            'contact_email', 'contact_phone',
            
            # Data Sekolah Asal
            'previous_school', 'previous_school_npsn', 'graduation_year',
            'program_choice',
            
            # Data Orang Tua
            # Data Orang Tua
            'father_name', 'father_occupation',
            'mother_name', 'mother_occupation',
            'parent_phone',

        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nama lengkap sesuai akta'
            }),
            'nisn': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '10',
                'placeholder': '(0123456789)'
            }),
            'birth_place': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(Jakarta)'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            
            'nik': forms.TextInput(attrs={
            'class': 'form-control',
            'maxlength': '16',
            'placeholder': '16 digit NIK'
            }),
            'religion': forms.Select(attrs={'class': 'form-select'}),
            
            # Kontak
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': '(contoh@gmail.com)',
                'required': True
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(08123456789)',
                'required': True
            }),
            
            # Sekolah
            'previous_school': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(SMP Negeri 1 Jakarta)'
            }),
            'previous_school_npsn': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '8',
                'placeholder': '(12345678)'
            }),
            'graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '(2000)',
                'min': '2000',
                'max': '2030'
            }),
            'program_choice': forms.Select(attrs={'class': 'form-select'}),
            
            # Alamat
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Jl. Contoh No. 123, RT 01/RW 02'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Jakarta Selatan'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'DKI Jakarta'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '5',
                'placeholder': '12345'
            }),
            
            # Orang Tua
            'father_name': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama Ayah'
            }),
            'father_occupation': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pekerjaan Ayah'
            }),
            'mother_name': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama Ibu'
            }),
            'mother_occupation': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pekerjaan Ibu'
            }),
            'parent_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '(08123456789)'
            }),
        }
        
        labels = {
            'contact_email': 'Email Anda',
            'contact_phone': 'No. HP Anda',
        }
        
        help_texts = {
            'contact_email': 'Email untuk notifikasi status pendaftaran',
            'contact_phone': 'Nomor HP yang bisa dihubungi (untuk cek status)',
            'nisn': 'Nomor Induk Siswa Nasional (10 digit)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add validators
        self.fields['nisn'].validators.append(validate_nisn)
        self.fields['graduation_year'].validators.append(validate_graduation_year)
        
        # Mark required fields
        required_fields = [
            'full_name', 'nisn', 'birth_place', 'birth_date', 'gender',
            'contact_email', 'contact_phone',
            'previous_school', 'graduation_year', 'program_choice',
            'address', 'city', 'province',

            'father_name', 'father_occupation',
            'mother_name', 'mother_occupation',
            'parent_phone',
        ]
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
    
    def clean_birth_date(self):
        """Validate tanggal lahir - untuk PKBM bisa lebih fleksibel"""
        from datetime import date
        birth_date = self.cleaned_data.get('birth_date')
        
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            
            # PKBM menerima semua usia (tidak ada batasan ketat)
            if age < 6:
                raise ValidationError('Umur minimal 6 tahun.')
            
            if age > 100:
                raise ValidationError('Tanggal lahir tidak valid.')
        
        return birth_date
    
    def clean_contact_phone(self):
        """Validasi format nomor HP"""
        phone = self.cleaned_data.get('contact_phone')
        
        # Remove spaces & dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Must start with 08 or +62
        if not (phone.startswith('08') or phone.startswith('+62') or phone.startswith('62')):
            raise ValidationError('Nomor HP harus diawali 08 atau +62')
        
        # Must be digits only (after +)
        clean_phone = phone.replace('+', '')
        if not clean_phone.isdigit():
            raise ValidationError('Nomor HP hanya boleh berisi angka')
        
        # Length check
        if len(clean_phone) < 10 or len(clean_phone) > 15:
            raise ValidationError('Panjang nomor HP tidak valid')
        
        return phone


class DocumentUploadForm(forms.ModelForm):
    """Form upload dokumen - PUBLIC"""
    
    class Meta:
        model = Document
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.registration = kwargs.pop('registration', None)
        super().__init__(*args, **kwargs)
        
        # Filter document_type yang sudah di-upload
        if self.registration:
            uploaded_types = self.registration.documents.values_list(
                'document_type', flat=True
            )
            choices = [
                (k, v) for k, v in Document.DocumentType.choices
                if k not in uploaded_types
            ]
            
            if not choices:
                self.fields['document_type'].choices = []
                self.fields['document_type'].widget.attrs['disabled'] = True
            else:
                self.fields['document_type'].choices = [('', '---------')] + choices
    
    def clean_file(self):
        """Validate file upload"""
        file = self.cleaned_data.get('file')
        
        if file:
            # Validate size
            validate_file_size(file)
            
            # Validate extension
            validate_file_extension(file)
            
            # Validate content (MIME type)
            validate_file_content(file)
        
        return file
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.registration:
            instance.registration = self.registration
        
        # Set metadata
        if instance.file:
            instance.original_filename = instance.file.name
            instance.file_size = instance.file.size
            
            # Get MIME type
            import magic
            instance.file.seek(0)
            file_content = instance.file.read(2048)
            instance.file.seek(0)
            instance.mime_type = magic.from_buffer(file_content, mime=True)
        
        if commit:
            instance.save()
        
        return instance