"""
Forms untuk authentication & user management.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser


class UserLoginForm(AuthenticationForm):
    """Form login dengan email"""
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
        })
    )
    
    error_messages = {
        'invalid_login': 'Email atau password salah.',
        'inactive': 'Akun ini tidak aktif.',
    }


class StudentRegistrationForm(UserCreationForm):
    """Form registrasi untuk siswa"""
    
    full_name = forms.CharField(
        label='Nama Lengkap',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama lengkap sesuai akta',
        })
    )
    
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
        })
    )
    
    phone = forms.CharField(
        label='Nomor HP',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(08123456789)',
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimal 8 karakter',
        })
    )
    
    password2 = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ulangi password',
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Email sudah terdaftar.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.UserRole.STUDENT
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form update profile user"""
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }