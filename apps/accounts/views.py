"""
Views untuk authentication & user management.
"""
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib import messages

from .forms import UserLoginForm, StudentRegistrationForm, ProfileUpdateForm
from .models import CustomUser


class LoginView(auth_views.LoginView):
    """Custom login view"""
    
    template_name = 'accounts/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect berdasarkan role user"""
        user = self.request.user
        
        if user.is_staff:
            # Staff → Staff Dashboard
            return reverse_lazy('registration:staff_dashboard')
        else:
            # Non-staff → Homepage
            return reverse_lazy('home')
    
    def form_invalid(self, form):
        messages.error(self.request, 'Email atau password salah.')
        return super().form_invalid(form)


class LogoutView(auth_views.LogoutView):
    """Custom logout view"""
    
    next_page = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        messages.success(request, 'Anda telah logout.')
        return super().dispatch(request, *args, **kwargs)


class RegisterView(CreateView):
    """Registrasi akun siswa baru"""
    
    model = CustomUser
    form_class = StudentRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def dispatch(self, request, *args, **kwargs):
        # Redirect jika sudah login
        if request.user.is_authenticated:
            return redirect('dashboard:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(
            self.request,
            'Registrasi berhasil! Silakan login dengan akun Anda.'
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Terjadi kesalahan. Periksa kembali form Anda.')
        return super().form_invalid(form)


class ProfileView(LoginRequiredMixin, UpdateView):
    """View & update profile user"""
    
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile berhasil diupdate.')
        return super().form_valid(form)