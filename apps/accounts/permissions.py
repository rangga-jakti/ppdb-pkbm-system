"""
Custom permissions and decorators for PPDB system.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def staff_required(function=None):
    """
    Decorator untuk views yang hanya bisa diakses oleh staff.
    Works with both function-based and class-based views.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get user from request
            user = request.user if hasattr(request, 'user') else None
            
            # Check authentication
            if not user or not user.is_authenticated:
                messages.error(request, 'Silakan login terlebih dahulu.')
                return redirect('accounts:login')
            
            # Check staff status
            if not user.is_staff:
                messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
                return redirect('home')
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    
    if function:
        return decorator(function)
    return decorator


def student_required(function):
    """
    Decorator untuk views yang hanya bisa diakses oleh siswa (non-staff).
    """
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        user = request.user if hasattr(request, 'user') else None
        
        if not user or not user.is_authenticated:
            messages.error(request, 'Silakan login terlebih dahulu.')
            return redirect('accounts:login')
        
        if user.is_staff:
            messages.warning(request, 'Akses ini khusus untuk siswa.')
            return redirect('registration:staff_dashboard')
        
        return function(request, *args, **kwargs)
    
    return wrapper


class PermissionManager:
    """
    Helper class untuk mixin-based permissions (class-based views).
    """
    
    @staticmethod
    def is_staff(user):
        """Check if user is staff"""
        return user.is_authenticated and user.is_staff
    
    @staticmethod
    def is_student(user):
        """Check if user is student (authenticated but not staff)"""
        return user.is_authenticated and not user.is_staff


class StaffRequiredMixin:
    """
    Mixin untuk class-based views yang memerlukan staff access.
    Usage: class MyView(LoginRequiredMixin, StaffRequiredMixin, View)
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Silakan login terlebih dahulu.')
            return redirect('accounts:login')
        
        if not request.user.is_staff:
            messages.error(request, 'Anda tidak memiliki akses ke halaman ini.')
            return redirect('home')
        
        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin:
    """
    Mixin untuk class-based views yang memerlukan student access.
    Usage: class MyView(LoginRequiredMixin, StudentRequiredMixin, View)
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Silakan login terlebih dahulu.')
            return redirect('accounts:login')
        
        if request.user.is_staff:
            messages.warning(request, 'Akses ini khusus untuk siswa.')
            return redirect('registration:staff_dashboard')
        
        return super().dispatch(request, *args, **kwargs)