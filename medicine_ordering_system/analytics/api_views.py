from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import time
import sqlite3

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
        
        # Generate forecast with retry logic
        forecasting_service = ARIMAForecastingService()
        
        max_retries = 3
        forecast = None
        for attempt in range(max_retries):
            try:
                forecast = forecasting_service.generate_forecast(
                    medicine_id, forecast_period, forecast_horizon
                )
                break  # Success, exit retry loop
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    raise e
        
        if forecast:
            try:
                # Generate inventory optimization
                optimization = forecasting_service.optimize_inventory_levels(forecast)
            except ValueError as e:
                if "Insufficient data points" in str(e):
                    # Get medicine name for better error message
                    try:
                        medicine = Medicine.objects.get(id=medicine_id)
                        medicine_name = medicine.name
                    except Medicine.DoesNotExist:
                        medicine_name = f"Medicine ID {medicine_id}"
                
                    error_response = {
                        'error': 'insufficient_data',
                        'message': f'Insufficient sales data for {medicine_name}. Need at least 30 data points for accurate forecasting.',
                        'medicine_name': medicine_name,
                        'required_data_points': 30,
                        'suggestion': 'Please ensure the medicine has sufficient sales history before generating forecasts.'
                    }
                    
                    return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
                else:
                    raise e
        
        # Generate forecast date labels for immediate display
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Get historical data to determine last date
        historical_data = forecasting_service.prepare_sales_data(
            medicine_id, forecast_period
        )
        last_historical_date = pd.to_datetime(historical_data['date'].iloc[-1])
        
        # Generate forecast period labels
        forecast_labels = []
        if forecast_period == 'daily':
            for i in range(1, forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i)
                forecast_labels.append(forecast_date.strftime('%b %d, %Y'))
        elif forecast_period == 'weekly':
            for i in range(1, forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(weeks=i)
                forecast_labels.append(f"Week of {forecast_date.strftime('%b %d, %Y')}")
        elif forecast_period == 'monthly':
            for i in range(1, forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i*30)  # Approximate month
                forecast_labels.append(forecast_date.strftime('%b %Y'))
        
        # Generate historical labels
        historical_labels = [d.strftime('%b %d, %Y') if hasattr(d, 'strftime') else str(d) for d in historical_data['date']]
        all_labels = historical_labels + forecast_labels
        
        return Response({
            'forecast_id': forecast.id,
            'medicine_name': forecast.medicine.name,
            'forecasted_demand': forecast.forecasted_demand,
            'confidence_intervals': forecast.confidence_intervals,
            'labels': all_labels,
            'forecast_labels': forecast_labels,
            'historical_data': {
                'values': historical_data['quantity'].tolist(),
                'labels': historical_labels
            },
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
                'expected_holding_cost': optimization.expected_holding_cost,
                'expected_stockout_cost': optimization.expected_stockout_cost,
                'total_expected_cost': optimization.total_expected_cost
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
        
        # Generate forecast date labels
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Get the last historical date
        last_historical_date = pd.to_datetime(historical_data['date'].iloc[-1])
        
        # Generate forecast period labels based on forecast_period
        forecast_labels = []
        if forecast.forecast_period == 'daily':
            for i in range(1, forecast.forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i)
                forecast_labels.append(forecast_date.strftime('%b %d, %Y'))
        elif forecast.forecast_period == 'weekly':
            for i in range(1, forecast.forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(weeks=i)
                forecast_labels.append(f"Week of {forecast_date.strftime('%b %d, %Y')}")
        elif forecast.forecast_period == 'monthly':
            for i in range(1, forecast.forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i*30)  # Approximate month
                forecast_labels.append(forecast_date.strftime('%b %Y'))
        
        # Combine historical and forecast labels
        historical_labels = [d.strftime('%b %d, %Y') if hasattr(d, 'strftime') else str(d) for d in historical_data['date']]
        all_labels = historical_labels + forecast_labels
        
        # Prepare data for visualization
        chart_data = {
            'labels': all_labels,
            'historical': {
                'dates': [str(d) for d in historical_data['date']],
                'values': historical_data['quantity'].tolist()
            },
            'forecast': {
                'values': forecast.forecasted_demand,
                'confidence_intervals': forecast.confidence_intervals,
                'labels': forecast_labels
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forecasts(request):
    """
    Get list of existing forecasts for extension
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get recent forecasts
        forecasts = DemandForecast.objects.select_related('medicine').order_by('-created_at')[:20]
        
        forecast_data = []
        for forecast in forecasts:
            forecast_data.append({
                'id': forecast.id,
                'medicine_name': forecast.medicine.name,
                'forecast_period': forecast.forecast_period,
                'forecast_horizon': forecast.forecast_horizon,
                'created_at': forecast.created_at.isoformat(),
                'accuracy': forecast.mape if forecast.mape else 0
            })
        
        return Response({'forecasts': forecast_data})
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extend_forecast(request):
    """
    Extend an existing forecast with additional periods
    """
    try:
        data = request.data
        forecast_id = data.get('forecast_id')
        extend_horizon = data.get('extend_horizon')
        extend_period = data.get('extend_period')
        
        if not all([forecast_id, extend_horizon, extend_period]):
            return Response(
                {'error': 'forecast_id, extend_horizon, and extend_period are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate horizon limits
        max_limits = {
            'daily': 30,
            'weekly': 52,
            'monthly': 24
        }
        
        if int(extend_horizon) > max_limits.get(extend_period, 12):
            return Response(
                {'error': f'Maximum extension for {extend_period} forecasts is {max_limits[extend_period]} periods'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the existing forecast
        try:
            existing_forecast = DemandForecast.objects.get(id=forecast_id)
        except DemandForecast.DoesNotExist:
            return Response(
                {'error': 'Forecast not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate extended forecast
        forecasting_service = ARIMAForecastingService()
        
        # Calculate new horizon (existing + extension)
        new_horizon = existing_forecast.forecast_horizon + int(extend_horizon)
        
        try:
            # Generate new forecast with extended horizon
            extended_forecast = forecasting_service.generate_forecast(
                existing_forecast.medicine.id,
                extend_period,
                new_horizon
            )
            
            # Update inventory optimization for the extended forecast
            optimization = forecasting_service.optimize_inventory_levels(extended_forecast)
            
        except ValueError as e:
            if "Insufficient data points" in str(e):
                return Response({
                    'error': 'insufficient_data',
                    'message': f'Insufficient sales data for {existing_forecast.medicine.name}. Need at least 30 data points for accurate forecasting.',
                    'medicine_name': existing_forecast.medicine.name,
                    'required_data_points': 30,
                    'suggestion': 'Please ensure the medicine has sufficient sales history before extending forecasts.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                raise e
        
        # Get the extended forecast data for the chart
        # We need to manually create the chart data since we can't call the API view directly
        historical_data = forecasting_service.prepare_sales_data(
            extended_forecast.medicine.id, 
            extend_period
        )
        
        # Generate forecast date labels
        from datetime import datetime, timedelta
        import pandas as pd
        
        # Get the last historical date
        last_historical_date = pd.to_datetime(historical_data['date'].iloc[-1])
        
        # Generate forecast period labels based on forecast_period
        forecast_labels = []
        if extend_period == 'daily':
            for i in range(1, new_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i)
                forecast_labels.append(forecast_date.strftime('%b %d, %Y'))
        elif extend_period == 'weekly':
            for i in range(1, new_horizon + 1):
                forecast_date = last_historical_date + timedelta(weeks=i)
                forecast_labels.append(f"Week of {forecast_date.strftime('%b %d, %Y')}")
        elif extend_period == 'monthly':
            for i in range(1, new_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i*30)  # Approximate month
                forecast_labels.append(forecast_date.strftime('%b %Y'))
        
        # Combine historical and forecast labels
        historical_labels = [d.strftime('%b %d, %Y') if hasattr(d, 'strftime') else str(d) for d in historical_data['date']]
        all_labels = historical_labels + forecast_labels
        
        # Prepare data for visualization (matching updateDemandForecastChart structure)
        forecast_data = {
            'labels': all_labels,
            'historical': {
                'values': historical_data['quantity'].tolist()
            },
            'forecast': {
                'values': extended_forecast.forecasted_demand,
                'labels': forecast_labels
            },
            'medicine_name': extended_forecast.medicine.name
        }
        
        return Response({
            'forecast_id': extended_forecast.id,
            'new_horizon': new_horizon,
            'extended_periods': extend_horizon,
            'message': f'Forecast extended successfully by {extend_horizon} {extend_period} periods',
            'forecast_data': forecast_data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_model_evaluation_data(request):
    """
    Get comprehensive model evaluation data for the model evaluation dashboard
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all forecasts with their metrics
        forecasts = DemandForecast.objects.filter(is_active=True).order_by('-created_at')
        
        # Calculate aggregate metrics
        aggregate_metrics = _calculate_aggregate_metrics(forecasts)
        
        # Get model performance distribution
        performance_distribution = _get_model_performance_distribution(forecasts)
        
        # Get medicine-specific performance
        medicine_performance = _get_medicine_performance(forecasts)
        
        # Get recent forecasts for detailed view
        recent_forecasts = []
        for forecast in forecasts[:20]:
            recent_forecasts.append({
                'id': forecast.id,
                'medicine_name': forecast.medicine.name,
                'forecast_period': forecast.forecast_period,
                'created_at': forecast.created_at.isoformat(),
                'mape': forecast.mape,
                'rmse': forecast.rmse,
                'mae': forecast.mae,
                'aic': forecast.aic,
                'bic': forecast.bic,
                'model_quality': forecast.model_quality,
                'arima_params': f"({forecast.arima_p},{forecast.arima_d},{forecast.arima_q})",
                'training_data_points': forecast.training_data_points,
            })
        
        return Response({
            'aggregate_metrics': aggregate_metrics,
            'performance_distribution': performance_distribution,
            'medicine_performance': medicine_performance,
            'recent_forecasts': recent_forecasts,
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_forecast(request, forecast_id):
    """
    Delete a specific forecast
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the forecast
        try:
            forecast = DemandForecast.objects.get(id=forecast_id)
        except DemandForecast.DoesNotExist:
            return Response(
                {'error': 'Forecast not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store forecast info for response
        forecast_info = {
            'id': forecast.id,
            'medicine_name': forecast.medicine.name,
            'forecast_period': forecast.forecast_period,
            'created_at': forecast.created_at.isoformat()
        }
        
        # Delete the forecast
        forecast.delete()
        
        return Response({
            'success': True,
            'message': f'Forecast for {forecast_info["medicine_name"]} deleted successfully',
            'deleted_forecast': forecast_info
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_forecast_on_demand(request):
    """
    Generate a new forecast on-demand for the Forecast-Only View
    Uses auto_arima to find the best model automatically
    """
    try:
        data = request.data
        medicine_id = data.get('medicine_id')
        forecast_period = data.get('forecast_period', 'weekly')
        forecast_horizon = data.get('forecast_horizon', 8)
        
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
        
        # Get medicine
        try:
            medicine = Medicine.objects.get(id=medicine_id)
        except Medicine.DoesNotExist:
            return Response(
                {'error': 'Medicine not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Generate forecast with retry logic
        forecasting_service = ARIMAForecastingService()
        
        max_retries = 3
        forecast = None
        for attempt in range(max_retries):
            try:
                forecast = forecasting_service.generate_forecast(
                    medicine_id, forecast_period, forecast_horizon
                )
                break  # Success, exit retry loop
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    raise e
        
        if not forecast:
            return Response(
                {'error': 'Failed to generate forecast'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Get historical data for chart
        historical_data = forecasting_service.prepare_sales_data(
            medicine_id, forecast_period
        )
        
        # Generate forecast date labels
        from datetime import datetime, timedelta
        import pandas as pd
        
        last_historical_date = pd.to_datetime(historical_data['date'].iloc[-1])
        
        # Generate forecast period labels
        forecast_labels = []
        if forecast_period == 'daily':
            for i in range(1, forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i)
                forecast_labels.append(forecast_date.strftime('%b %d, %Y'))
        elif forecast_period == 'weekly':
            for i in range(1, forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(weeks=i)
                forecast_labels.append(f"Week of {forecast_date.strftime('%b %d, %Y')}")
        elif forecast_period == 'monthly':
            for i in range(1, forecast_horizon + 1):
                forecast_date = last_historical_date + timedelta(days=i*30)
                forecast_labels.append(forecast_date.strftime('%b %Y'))
        
        # Generate historical labels
        historical_labels = [d.strftime('%b %d, %Y') if hasattr(d, 'strftime') else str(d) for d in historical_data['date']]
        all_labels = historical_labels + forecast_labels
        
        # Prepare chart data
        chart_data = {
            'labels': all_labels,
            'historical': {
                'values': historical_data['quantity'].tolist(),
                'labels': historical_labels
            },
            'forecast': {
                'values': forecast.forecasted_demand,
                'labels': forecast_labels
            }
        }
        
        return Response({
            'success': True,
            'forecast_id': forecast.id,
            'medicine_name': medicine.name,
            'medicine_id': medicine.id,
            'chart_data': chart_data,
            'model_info': {
                'arima_params': f"ARIMA({forecast.arima_p},{forecast.arima_d},{forecast.arima_q})",
                'aic': forecast.aic,
                'bic': forecast.bic,
                'mape': forecast.mape,
                'rmse': forecast.rmse,
                'mae': forecast.mae,
                'model_quality': forecast.model_quality
            },
            'forecast_period': forecast_period,
            'forecast_horizon': forecast_horizon
        })
        
    except ValueError as e:
        if "Insufficient data points" in str(e):
            return Response({
                'error': 'insufficient_data',
                'message': f'Insufficient sales data for {medicine.name}. Need at least 30 data points for accurate forecasting.',
                'medicine_name': medicine.name,
                'required_data_points': 30,
                'suggestion': 'Please ensure the medicine has sufficient sales history before generating forecasts.'
            }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_forecast_details(request, forecast_id):
    """
    Get detailed information about a specific forecast
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the forecast
        try:
            forecast = DemandForecast.objects.get(id=forecast_id)
        except DemandForecast.DoesNotExist:
            return Response(
                {'error': 'Forecast not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get related optimization data
        optimization = InventoryOptimization.objects.filter(
            demand_forecast=forecast
        ).first()
        
        forecast_data = {
            'id': forecast.id,
            'medicine_name': forecast.medicine.name,
            'medicine_id': forecast.medicine.id,
            'forecast_period': forecast.forecast_period,
            'forecast_horizon': forecast.forecast_horizon,
            'created_at': forecast.created_at.isoformat(),
            'arima_params': {
                'p': forecast.arima_p,
                'd': forecast.arima_d,
                'q': forecast.arima_q,
            },
            'model_metrics': {
                'aic': forecast.aic,
                'bic': forecast.bic,
                'rmse': forecast.rmse,
                'mae': forecast.mae,
                'mape': forecast.mape,
            },
            'model_quality': forecast.model_quality,
            'forecasted_demand': forecast.forecasted_demand,
            'confidence_intervals': forecast.confidence_intervals,
            'training_data': {
                'start_date': forecast.training_data_start.isoformat(),
                'end_date': forecast.training_data_end.isoformat(),
                'data_points': forecast.training_data_points,
            },
            'optimization': None,
        }
        
        if optimization:
            forecast_data['optimization'] = {
                'service_level': float(optimization.service_level),
                'lead_time_days': optimization.lead_time_days,
                'holding_cost_percentage': float(optimization.holding_cost_percentage),
                'optimal_reorder_point': optimization.optimal_reorder_point,
                'optimal_order_quantity': optimization.optimal_order_quantity,
                'optimal_maximum_stock': optimization.optimal_maximum_stock,
                'safety_stock': optimization.safety_stock,
                'expected_holding_cost': float(optimization.expected_holding_cost),
                'expected_stockout_cost': float(optimization.expected_stockout_cost),
                'total_expected_cost': float(optimization.total_expected_cost),
            }
        
        return Response(forecast_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _calculate_aggregate_metrics(forecasts):
    """Helper function to calculate aggregate model performance metrics"""
    if not forecasts.exists():
        return {
            'total_forecasts': 0,
            'avg_mape': 0,
            'avg_rmse': 0,
            'avg_mae': 0,
            'avg_aic': 0,
            'avg_bic': 0,
            'excellent_models': 0,
            'good_models': 0,
            'fair_models': 0,
            'poor_models': 0,
        }
    
    # Calculate averages
    avg_mape = forecasts.aggregate(avg=models.Avg('mape'))['avg'] or 0
    avg_rmse = forecasts.aggregate(avg=models.Avg('rmse'))['avg'] or 0
    avg_mae = forecasts.aggregate(avg=models.Avg('mae'))['avg'] or 0
    avg_aic = forecasts.aggregate(avg=models.Avg('aic'))['avg'] or 0
    avg_bic = forecasts.aggregate(avg=models.Avg('bic'))['avg'] or 0
    
    # Count by quality
    excellent_models = forecasts.filter(mape__lt=10).count()
    good_models = forecasts.filter(mape__gte=10, mape__lt=20).count()
    fair_models = forecasts.filter(mape__gte=20, mape__lt=30).count()
    poor_models = forecasts.filter(mape__gte=30).count()
    
    return {
        'total_forecasts': forecasts.count(),
        'avg_mape': round(avg_mape, 2),
        'avg_rmse': round(avg_rmse, 2),
        'avg_mae': round(avg_mae, 2),
        'avg_aic': round(avg_aic, 2),
        'avg_bic': round(avg_bic, 2),
        'excellent_models': excellent_models,
        'good_models': good_models,
        'fair_models': fair_models,
        'poor_models': poor_models,
    }


def _get_model_performance_distribution(forecasts):
    """Helper function to get model performance distribution data"""
    # Performance by period type
    period_performance = {}
    for period in ['daily', 'weekly', 'monthly']:
        period_forecasts = forecasts.filter(forecast_period=period)
        if period_forecasts.exists():
            period_performance[period] = {
                'count': period_forecasts.count(),
                'avg_mape': round(period_forecasts.aggregate(avg=models.Avg('mape'))['avg'] or 0, 2),
                'avg_rmse': round(period_forecasts.aggregate(avg=models.Avg('rmse'))['avg'] or 0, 2),
            }
    
    return {
        'period_performance': period_performance,
    }


def _get_medicine_performance(forecasts):
    """Helper function to get medicine-specific performance metrics"""
    # Top performing medicines (lowest MAPE)
    top_performers = []
    for forecast in forecasts.order_by('mape')[:10]:
        top_performers.append({
            'medicine_name': forecast.medicine.name,
            'forecast_period': forecast.forecast_period,
            'mape': forecast.mape,
            'model_quality': forecast.model_quality,
        })
    
    # Worst performing medicines (highest MAPE)
    worst_performers = []
    for forecast in forecasts.order_by('-mape')[:10]:
        worst_performers.append({
            'medicine_name': forecast.medicine.name,
            'forecast_period': forecast.forecast_period,
            'mape': forecast.mape,
            'model_quality': forecast.model_quality,
        })
    
    return {
        'top_performers': top_performers,
        'worst_performers': worst_performers,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_best_forecast_auto(request):
    """
    Automatically generate forecast using the best model for a specific medicine or all medicines
    """
    try:
        # Check permissions
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get medicine_id from query parameters
        medicine_id = request.GET.get('medicine_id')
        
        if medicine_id:
            # Get specific medicine
            try:
                medicines = [Medicine.objects.get(id=medicine_id, is_active=True)]
            except Medicine.DoesNotExist:
                return Response(
                    {'error': 'Medicine not found or inactive'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get all medicines with sufficient data
            medicines = Medicine.objects.filter(is_active=True)
        best_forecast = None
        best_medicine = None
        best_metrics = None
        
        forecasting_service = ARIMAForecastingService()
        
        # Test different period/horizon combinations to find the best
        period_horizon_combinations = [
            ('weekly', 8),
            ('weekly', 12),
            ('weekly', 16),
            ('monthly', 6),
            ('monthly', 12),
            ('daily', 7),
            ('daily', 14)
        ]
        
        best_score = float('inf')
        
        for medicine in medicines:
            for period, horizon in period_horizon_combinations:
                try:
                    # Test if medicine has sufficient data
                    historical_data = forecasting_service.prepare_sales_data(medicine.id, period)
                    
                    if len(historical_data) < 30:  # Minimum data requirement
                        continue
                    
                    # Generate forecast to test model quality
                    forecast = forecasting_service.generate_forecast(medicine.id, period, horizon)
                    
                    # Calculate composite score (lower is better)
                    # Weight MAPE more heavily as it's percentage-based
                    composite_score = (
                        forecast.mape * 0.4 +  # 40% weight for MAPE
                        (forecast.rmse / max(historical_data['quantity'].mean(), 1)) * 100 * 0.3 +  # 30% weight for normalized RMSE
                        forecast.aic / 1000 * 0.2 +  # 20% weight for AIC (normalized)
                        forecast.bic / 1000 * 0.1    # 10% weight for BIC (normalized)
                    )
                    
                    if composite_score < best_score:
                        best_score = composite_score
                        best_forecast = forecast
                        best_medicine = medicine
                        best_metrics = {
                            'period': period,
                            'horizon': horizon,
                            'mape': forecast.mape,
                            'rmse': forecast.rmse,
                            'aic': forecast.aic,
                            'bic': forecast.bic,
                            'composite_score': composite_score
                        }
                        
                except Exception as e:
                    # Skip this combination if it fails
                    continue
        
        if not best_forecast:
            if medicine_id:
                return Response(
                    {'error': f'No sufficient data found for the selected medicine. Need at least 30 data points for accurate forecasting.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            else:
                return Response(
                    {'error': 'No medicines with sufficient data found for forecasting'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Get historical data for the best forecast
        historical_data = forecasting_service.prepare_sales_data(
            best_medicine.id, best_metrics['period']
        )
        
        # Generate forecast date labels
        from datetime import datetime, timedelta
        import pandas as pd
        
        last_historical_date = pd.to_datetime(historical_data['date'].iloc[-1])
        
        # Generate forecast period labels
        forecast_labels = []
        if best_metrics['period'] == 'daily':
            for i in range(1, best_metrics['horizon'] + 1):
                forecast_date = last_historical_date + timedelta(days=i)
                forecast_labels.append(forecast_date.strftime('%b %d, %Y'))
        elif best_metrics['period'] == 'weekly':
            for i in range(1, best_metrics['horizon'] + 1):
                forecast_date = last_historical_date + timedelta(weeks=i)
                forecast_labels.append(f"Week of {forecast_date.strftime('%b %d, %Y')}")
        elif best_metrics['period'] == 'monthly':
            for i in range(1, best_metrics['horizon'] + 1):
                forecast_date = last_historical_date + timedelta(days=i*30)
                forecast_labels.append(forecast_date.strftime('%b %Y'))
        
        # Generate historical labels
        historical_labels = [d.strftime('%b %d, %Y') if hasattr(d, 'strftime') else str(d) for d in historical_data['date']]
        all_labels = historical_labels + forecast_labels
        
        # Prepare chart data
        chart_data = {
            'labels': all_labels,
            'historical': {
                'values': historical_data['quantity'].tolist(),
                'labels': historical_labels
            },
            'forecast': {
                'values': best_forecast.forecasted_demand,
                'labels': forecast_labels
            },
            'model_info': {
                'arima_params': f"ARIMA({best_forecast.arima_p},{best_forecast.arima_d},{best_forecast.arima_q})",
                'aic': best_forecast.aic,
                'bic': best_forecast.bic,
                'mape': best_forecast.mape,
                'rmse': best_forecast.rmse,
                'mae': best_forecast.mae,
                'model_quality': best_forecast.model_quality
            }
        }
        
        return Response({
            'success': True,
            'forecast_id': best_forecast.id,
            'medicine_name': best_medicine.name,
            'medicine_id': best_medicine.id,
            'chart_data': chart_data,
            'model_info': chart_data['model_info'],
            'forecast_period': best_metrics['period'],
            'forecast_horizon': best_metrics['horizon'],
            'selection_reason': f"Best model selected based on composite score: {best_metrics['composite_score']:.2f} (MAPE: {best_metrics['mape']:.2f}%, RMSE: {best_metrics['rmse']:.2f})"
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )