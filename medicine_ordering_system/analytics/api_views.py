from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from .models import DemandForecast, InventoryOptimization, SalesTrend, CustomerAnalytics, SystemMetrics
from .services import ARIMAForecastingService, SupplyChainOptimizer
from inventory.models import Medicine
from orders.models import Order


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_forecast(request):
    """
    Generate demand forecast for a medicine
    """
    try:
        data = request.data
        medicine_id = data.get('medicine_id')
        forecast_period = data.get('forecast_period', 'weekly')
        forecast_horizon = data.get('forecast_horizon', 4)
        
        if not medicine_id:
            return Response(
                {'error': 'medicine_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate forecast
        forecasting_service = ARIMAForecastingService()
        forecast = forecasting_service.generate_forecast(
            medicine_id, forecast_period, forecast_horizon
        )
        
        # Generate inventory optimization
        optimization = forecasting_service.optimize_inventory_levels(forecast)
        
        return Response({
            'forecast_id': forecast.id,
            'medicine_name': forecast.medicine.name,
            'forecasted_demand': forecast.forecasted_demand,
            'confidence_intervals': forecast.confidence_intervals,
            'model_metrics': {
                'aic': forecast.aic,
                'bic': forecast.bic,
                'rmse': forecast.rmse,
                'mae': forecast.mae,
                'mape': forecast.mape,
            },
            'optimization': {
                'optimal_reorder_point': optimization.optimal_reorder_point,
                'optimal_order_quantity': optimization.optimal_order_quantity,
                'safety_stock': optimization.safety_stock,
            }
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forecast_data(request, forecast_id):
    """
    Get forecast data for visualization
    """
    try:
        forecast = get_object_or_404(DemandForecast, id=forecast_id)
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get historical data for comparison
        forecasting_service = ARIMAForecastingService()
        historical_data = forecasting_service.prepare_sales_data(
            forecast.medicine.id, 
            forecast.forecast_period
        )
        
        # Prepare data for visualization
        chart_data = {
            'historical': {
                'dates': [str(d) for d in historical_data['date']],
                'values': historical_data['quantity'].tolist()
            },
            'forecast': {
                'values': forecast.forecasted_demand,
                'confidence_intervals': forecast.confidence_intervals
            },
            'model_info': {
                'arima_params': f"ARIMA({forecast.arima_p},{forecast.arima_d},{forecast.arima_q})",
                'aic': forecast.aic,
                'bic': forecast.bic,
                'rmse': forecast.rmse,
                'mae': forecast.mae,
                'mape': forecast.mape,
            }
        }
        
        return Response(chart_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sales_trends(request, medicine_id):
    """
    Get sales trends for a medicine
    """
    try:
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        period_type = request.GET.get('period_type', 'weekly')
        days_back = int(request.GET.get('days_back', 90))
        
        start_date = timezone.now().date() - timedelta(days=days_back)
        
        trends = SalesTrend.objects.filter(
            medicine=medicine,
            period_type=period_type,
            period_date__gte=start_date
        ).order_by('period_date')
        
        chart_data = {
            'dates': [str(trend.period_date) for trend in trends],
            'quantities': [trend.quantity_sold for trend in trends],
            'revenues': [float(trend.revenue) for trend in trends],
            'growth_rates': [trend.growth_rate for trend in trends if trend.growth_rate is not None],
            'trend_directions': [trend.trend_direction for trend in trends if trend.trend_direction]
        }
        
        return Response(chart_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_inventory_optimization(request, medicine_id):
    """
    Get inventory optimization recommendations
    """
    try:
        medicine = get_object_or_404(Medicine, id=medicine_id)
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get latest optimization
        optimization = InventoryOptimization.objects.filter(
            medicine=medicine,
            is_active=True
        ).order_by('-calculated_at').first()
        
        if not optimization:
            return Response(
                {'error': 'No optimization data available'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        optimization_data = {
            'medicine_name': medicine.name,
            'current_stock': medicine.current_stock,
            'reorder_point': medicine.reorder_point,
            'optimal_reorder_point': optimization.optimal_reorder_point,
            'optimal_order_quantity': optimization.optimal_order_quantity,
            'optimal_maximum_stock': optimization.optimal_maximum_stock,
            'safety_stock': optimization.safety_stock,
            'service_level': float(optimization.service_level),
            'expected_costs': {
                'holding_cost': float(optimization.expected_holding_cost),
                'stockout_cost': float(optimization.expected_stockout_cost),
                'total_cost': float(optimization.total_expected_cost),
            },
            'calculated_at': optimization.calculated_at,
        }
        
        return Response(optimization_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_system_metrics(request):
    """
    Get system-wide metrics
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        period_type = request.GET.get('period_type', 'daily')
        days_back = int(request.GET.get('days_back', 30))
        
        start_date = timezone.now().date() - timedelta(days=days_back)
        
        metrics = SystemMetrics.objects.filter(
            period_type=period_type,
            period_date__gte=start_date
        ).order_by('period_date')
        
        chart_data = {
            'dates': [str(metric.period_date) for metric in metrics],
            'total_orders': [metric.total_orders for metric in metrics],
            'total_revenue': [float(metric.total_revenue) for metric in metrics],
            'total_customers': [metric.total_customers for metric in metrics],
            'inventory_turnover': [metric.inventory_turnover for metric in metrics],
            'low_stock_items': [metric.low_stock_items for metric in metrics],
            'customer_satisfaction': [metric.customer_satisfaction_score for metric in metrics if metric.customer_satisfaction_score],
        }
        
        return Response(chart_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_bulk_forecasts(request):
    """
    Generate forecasts for multiple medicines
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        data = request.data
        medicine_ids = data.get('medicine_ids', [])
        forecast_period = data.get('forecast_period', 'weekly')
        forecast_horizon = data.get('forecast_horizon', 4)
        
        if not medicine_ids:
            return Response(
                {'error': 'medicine_ids is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate bulk forecasts
        forecasting_service = ARIMAForecastingService()
        forecasts = forecasting_service.generate_bulk_forecasts(
            medicine_ids, forecast_period, forecast_horizon
        )
        
        results = []
        for forecast in forecasts:
            results.append({
                'forecast_id': forecast.id,
                'medicine_name': forecast.medicine.name,
                'model_quality': forecast.model_quality,
                'mape': forecast.mape,
            })
        
        return Response({
            'success': True,
            'forecasts_generated': len(results),
            'results': results
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reorder_alerts(request):
    """
    Get reorder alerts for low stock items
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        optimizer = SupplyChainOptimizer()
        alerts = optimizer.generate_reorder_alerts()
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                'medicine_id': alert['medicine'].id,
                'medicine_name': alert['medicine'].name,
                'current_stock': alert['current_stock'],
                'reorder_point': alert['reorder_point'],
                'suggested_quantity': alert['suggested_quantity'],
                'priority': alert['priority'],
                'is_critical': alert['current_stock'] == 0,
            })
        
        return Response({
            'alerts': alert_data,
            'total_alerts': len(alert_data),
            'critical_alerts': len([a for a in alert_data if a['is_critical']])
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
