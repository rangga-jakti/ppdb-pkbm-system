from django.urls import path
from . import views, webhooks

app_name = 'payments'

urlpatterns = [
    # Create payment
    path('create/<uuid:registration_id>/', views.CreatePaymentView.as_view(), name='create'),
    
    # Payment instructions
    path('<uuid:pk>/instructions/', views.PaymentInstructionsView.as_view(), name='instructions'),
    
    # Payment status
    path('<uuid:pk>/status/', views.PaymentStatusView.as_view(), name='status'),
    
    # TAMBAHKAN INI (SIMULATE - TESTING)
    path('<uuid:pk>/simulate/', views.simulate_payment, name='simulate'),
    
    # Webhook
    path('webhook/midtrans/', views.midtrans_webhook, name='midtrans_webhook'),
]
