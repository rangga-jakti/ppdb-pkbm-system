from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect homepage
    path('', RedirectView.as_view(url='/registration/create/', permanent=False), name='home'),
    
    # Apps
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('registration/', include('apps.registration.urls', namespace='registration')),
    path('payments/', include('apps.payments.urls', namespace='payments')),
]

# Media & Static (development)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# HAPUS SEMUA handler403, handler404, handler500
# Django akan pakai default error pages