from django.urls import path, include
from . import views, api_views

app_name = 'analytics'

urlpatterns = [
    # Dashboard views
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('forecast-only/', views.ForecastOnlyView.as_view(), name='forecast_only'),
    path('model-evaluation/', views.ModelEvaluationView.as_view(), name='model_evaluation'),
    path('arima-demonstration/', views.arima_demonstration_view, name='arima_demonstration'),
    path('arima-step-by-step/', views.arima_step_by_step_view, name='arima_step_by_step'),
    
    # API endpoints
    path('api/forecast/generate/', api_views.generate_forecast, name='api_generate_forecast'),
    path('api/forecast/<int:forecast_id>/data/', api_views.get_forecast_data, name='api_forecast_data'),
    path('api/forecast/bulk/', api_views.generate_bulk_forecasts, name='api_bulk_forecasts'),
    path('api/sales-trends/<int:medicine_id>/', api_views.get_sales_trends, name='api_sales_trends'),
    path('api/inventory-optimization/<int:medicine_id>/', api_views.get_inventory_optimization, name='api_inventory_optimization'),
    path('api/system-metrics/', api_views.get_system_metrics, name='api_system_metrics'),
    path('api/reorder-alerts/', api_views.get_reorder_alerts, name='api_reorder_alerts'),
    path('api/forecasts/', api_views.get_forecasts, name='api_get_forecasts'),
    path('api/forecast/extend/', api_views.extend_forecast, name='api_extend_forecast'),
    path('api/model-evaluation/', api_views.get_model_evaluation_data, name='api_model_evaluation'),
    path('api/forecast/<int:forecast_id>/details/', api_views.get_forecast_details, name='api_forecast_details'),
    path('api/forecast/<int:forecast_id>/delete/', api_views.delete_forecast, name='api_delete_forecast'),
    path('api/forecast/generate-on-demand/', api_views.generate_forecast_on_demand, name='api_generate_forecast_on_demand'),
    path('api/forecast/best-auto/', api_views.get_best_forecast_auto, name='api_best_forecast_auto'),
    path('api/arima-analysis/', views.arima_analysis_data, name='api_arima_analysis'),
    path('api/arima-step-analysis/', views.arima_step_analysis_data, name='api_arima_step_analysis'),
]
