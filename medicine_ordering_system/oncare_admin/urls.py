from django.urls import path, include
from . import views

app_name = 'oncare_admin'

urlpatterns = [
    # Dashboard
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    
    # System management
    path('system-health/', views.SystemHealthView.as_view(), name='system_health'),
    path('maintenance/', views.MaintenanceListView.as_view(), name='maintenance_list'),
    path('maintenance/create/', views.MaintenanceCreateView.as_view(), name='maintenance_create'),
    path('maintenance/<int:pk>/', views.MaintenanceDetailView.as_view(), name='maintenance_detail'),
    
    # Reports and analytics
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/create/', views.ReportCreateView.as_view(), name='report_create'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('reports/<int:pk>/execute/', views.ReportExecuteView.as_view(), name='report_execute'),
    
    # Dashboard widgets
    path('widgets/', views.WidgetListView.as_view(), name='widget_list'),
    path('widgets/create/', views.WidgetCreateView.as_view(), name='widget_create'),
    path('widgets/<int:pk>/edit/', views.WidgetEditView.as_view(), name='widget_edit'),
    
    # Alerts and notifications
    path('alerts/', views.AlertListView.as_view(), name='alert_list'),
    path('alerts/<int:pk>/', views.AlertDetailView.as_view(), name='alert_detail'),
    path('alerts/<int:pk>/acknowledge/', views.AlertAcknowledgeView.as_view(), name='alert_acknowledge'),
    path('alerts/<int:pk>/resolve/', views.AlertResolveView.as_view(), name='alert_resolve'),
    
    # User activity
    path('user-activity/', views.UserActivityView.as_view(), name='user_activity'),
    
    # API endpoints
    path('api/dashboard-data/', views.DashboardDataAPIView.as_view(), name='api_dashboard_data'),
    path('api/system-metrics/', views.SystemMetricsAPIView.as_view(), name='api_system_metrics'),
    path('api/alerts/', views.AlertAPIView.as_view(), name='api_alerts'),
    path('api/reports/', views.ReportAPIView.as_view(), name='api_reports'),
]
