# apps/accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model dengan email sebagai username.
    Mendukung role-based access (siswa vs panitia).
    """
    
    class UserRole(models.TextChoices):
        STUDENT = 'STUDENT', _('Siswa')
        STAFF = 'STAFF', _('Panitia')
        ADMIN = 'ADMIN', _('Administrator')
    
    email = models.EmailField(_('Email'), unique=True, db_index=True)
    full_name = models.CharField(_('Nama Lengkap'), max_length=255)
    phone = models.CharField(_('Nomor HP'), max_length=20, blank=True)
    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Django admin access
    
    date_joined = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email', 'role']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    def is_student(self):
        return self.role == self.UserRole.STUDENT
    
    def is_panitia(self):
        return self.role in [self.UserRole.STAFF, self.UserRole.ADMIN]