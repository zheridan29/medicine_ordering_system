from django.urls import path, include
from . import views

app_name = 'audits'

urlpatterns = [
    # Dashboard
    path('', views.AuditDashboardView.as_view(), name='dashboard'),
    
    # Audit logs
    path('logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('logs/<int:pk>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    
    # Security events
    path('security-events/', views.SecurityEventListView.as_view(), name='security_event_list'),
    path('security-events/<int:pk>/', views.SecurityEventDetailView.as_view(), name='security_event_detail'),
    path('security-events/<int:pk>/resolve/', views.SecurityEventResolveView.as_view(), name='security_event_resolve'),
    
    # System health
    path('system-health/', views.SystemHealthListView.as_view(), name='system_health_list'),
    path('system-health/metrics/', views.SystemHealthMetricsView.as_view(), name='system_health_metrics'),
    
    # Compliance
    path('compliance/', views.ComplianceLogListView.as_view(), name='compliance_log_list'),
    path('compliance/<int:pk>/', views.ComplianceLogDetailView.as_view(), name='compliance_log_detail'),
    
    # API endpoints
    path('api/audit-logs/', views.AuditLogAPIView.as_view(), name='api_audit_logs'),
    path('api/security-events/', views.SecurityEventAPIView.as_view(), name='api_security_events'),
    path('api/system-health/', views.SystemHealthAPIView.as_view(), name='api_system_health'),
    path('api/compliance/', views.ComplianceAPIView.as_view(), name='api_compliance'),
]
