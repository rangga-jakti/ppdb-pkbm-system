from django.urls import path
from . import views

app_name = 'registration'

urlpatterns = [
    # ============================================
    # PUBLIC ROUTES
    # ============================================
    
    # Create registration
    path('create/', views.CreateRegistrationView.as_view(), name='create'),
    
    # Upload documents
    path('<uuid:pk>/documents/', views.DocumentUploadView.as_view(), name='documents'),
    
    # Review
    path('<uuid:pk>/review/', views.ReviewRegistrationView.as_view(), name='review'),
    
    # Submit (POST only)
    path('<uuid:pk>/submit/', views.submit_registration_view, name='submit'),
    
    # Check status
    path('check-status/', views.check_status_view, name='check_status'),
    
    # ============================================
    # STAFF ONLY ROUTES
    # ============================================
    
    # Dashboard
    path('staff/dashboard/', views.StaffDashboardView.as_view(), name='staff_dashboard'),
    
    # List registrations
    path('staff/list/', views.RegistrationListView.as_view(), name='staff_list'),
    
    # Detail for verification
    path('staff/<uuid:pk>/', views.StaffRegistrationDetailView.as_view(), name='staff_detail'),
    
    # Verify (approve/reject)
    path('staff/<uuid:pk>/verify/', views.VerifyRegistrationView.as_view(), name='staff_verify'),
    
    # Bulk actions
    path('staff/bulk-verify/', views.BulkVerifyView.as_view(), name='staff_bulk_verify'),
    
    # Export Excel
    path('staff/export/', views.ExportRegistrationsView.as_view(), name='staff_export'),
    
    # Delete document
    path('document/<uuid:doc_id>/delete/', views.delete_document_view, name='delete_document'),

]