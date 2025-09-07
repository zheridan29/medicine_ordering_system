from django.urls import path, include
from . import views

app_name = 'common'

urlpatterns = [
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/<int:pk>/mark-read/', views.NotificationMarkReadView.as_view(), name='notification_mark_read'),
    
    # System configuration
    path('config/', views.ConfigurationListView.as_view(), name='config_list'),
    path('config/<int:pk>/edit/', views.ConfigurationEditView.as_view(), name='config_edit'),
    
    # File uploads
    path('uploads/', views.FileUploadListView.as_view(), name='file_upload_list'),
    path('uploads/<int:pk>/', views.FileUploadDetailView.as_view(), name='file_upload_detail'),
    
    # Email templates
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email_template_list'),
    path('email-templates/create/', views.EmailTemplateCreateView.as_view(), name='email_template_create'),
    path('email-templates/<int:pk>/edit/', views.EmailTemplateEditView.as_view(), name='email_template_edit'),
    
    # API endpoints
    path('api/notifications/', views.NotificationAPIView.as_view(), name='api_notifications'),
    path('api/config/', views.ConfigurationAPIView.as_view(), name='api_config'),
    path('api/file-uploads/', views.FileUploadAPIView.as_view(), name='api_file_uploads'),
]
