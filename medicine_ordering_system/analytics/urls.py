from django.urls import path, include
from . import views, api_views

app_name = 'analytics'

urlpatterns = [
    # Dashboard views
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/forecast/generate/', api_views.generate_forecast, name='api_generate_forecast'),
    path('api/forecast/<int:forecast_id>/data/', api_views.get_forecast_data, name='api_forecast_data'),
    path('api/forecast/bulk/', api_views.generate_bulk_forecasts, name='api_bulk_forecasts'),
    path('api/sales-trends/<int:medicine_id>/', api_views.get_sales_trends, name='api_sales_trends'),
    path('api/inventory-optimization/<int:medicine_id>/', api_views.get_inventory_optimization, name='api_inventory_optimization'),
    path('api/system-metrics/', api_views.get_system_metrics, name='api_system_metrics'),
    path('api/reorder-alerts/', api_views.get_reorder_alerts, name='api_reorder_alerts'),
]
