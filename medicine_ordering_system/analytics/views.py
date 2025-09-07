from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db import models
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import DemandForecast, InventoryOptimization, SalesTrend, CustomerAnalytics, SystemMetrics
from .services import ARIMAForecastingService, SupplyChainOptimizer
from inventory.models import Medicine, Category
from orders.models import Order, OrderItem
from accounts.models import User


class AnalyticsDashboardView(TemplateView):
    """
    Main analytics dashboard
    """
    template_name = 'analytics/dashboard.html'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user role-based data
        user = self.request.user
        
        if user.is_admin or user.is_pharmacist_admin:
            # Admin/Pharmacist dashboard
            context.update(self._get_admin_dashboard_data())
        else:
            # Customer dashboard
            context.update(self._get_customer_dashboard_data())
        
        return context
    
    def _get_admin_dashboard_data(self):
        """Get data for admin/pharmacist dashboard"""
        # Recent forecasts
        recent_forecasts = DemandForecast.objects.filter(
            is_active=True
        ).order_by('-created_at')[:10]
        
        # Low stock medicines
        low_stock_medicines = Medicine.objects.filter(
            current_stock__lte=models.F('reorder_point'),
            is_active=True
        )[:10]
        
        # Recent sales trends
        recent_trends = SalesTrend.objects.filter(
            period_date__gte=timezone.now().date() - timedelta(days=30)
        ).order_by('-period_date')[:20]
        
        # System metrics
        today_metrics = SystemMetrics.objects.filter(
            period_type='daily',
            period_date=timezone.now().date()
        ).first()
        
        return {
            'recent_forecasts': recent_forecasts,
            'low_stock_medicines': low_stock_medicines,
            'recent_trends': recent_trends,
            'today_metrics': today_metrics,
        }
    
    def _get_customer_dashboard_data(self):
        """Get data for customer dashboard"""
        # Customer's order history
        customer_orders = Order.objects.filter(
            customer=self.request.user
        ).order_by('-created_at')[:10]
        
        # Customer analytics
        customer_analytics = CustomerAnalytics.objects.filter(
            customer=self.request.user
        ).first()
        
        return {
            'customer_orders': customer_orders,
            'customer_analytics': customer_analytics,
        }


class ModelEvaluationView(TemplateView):
    """
    Model evaluation dashboard for admins to assess forecast model performance
    """
    template_name = 'analytics/model_evaluation.html'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        # Only allow admin and pharmacist access
        if not (self.request.user.is_admin or self.request.user.is_pharmacist_admin):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Access denied. Admin or Pharmacist privileges required.")
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all forecasts with their metrics
        forecasts = DemandForecast.objects.filter(is_active=True).order_by('-created_at')
        
        # Calculate aggregate metrics
        context.update(self._calculate_aggregate_metrics(forecasts))
        
        # Get recent forecasts for detailed view
        context['recent_forecasts'] = forecasts[:20]
        
        # Get model performance distribution
        context.update(self._get_model_performance_distribution(forecasts))
        
        # Get medicine-specific performance
        context.update(self._get_medicine_performance(forecasts))
        
        return context
    
    def _calculate_aggregate_metrics(self, forecasts):
        """Calculate aggregate model performance metrics"""
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
    
    def _get_model_performance_distribution(self, forecasts):
        """Get model performance distribution data for charts"""
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
        
        # Performance over time (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_forecasts = forecasts.filter(created_at__gte=thirty_days_ago)
        
        # Group by date for time series
        daily_performance = {}
        for i in range(30):
            date = (timezone.now() - timedelta(days=i)).date()
            day_forecasts = recent_forecasts.filter(created_at__date=date)
            if day_forecasts.exists():
                daily_performance[date.isoformat()] = {
                    'count': day_forecasts.count(),
                    'avg_mape': round(day_forecasts.aggregate(avg=models.Avg('mape'))['avg'] or 0, 2),
                }
        
        return {
            'period_performance': period_performance,
            'daily_performance': daily_performance,
        }
    
    def _get_medicine_performance(self, forecasts):
        """Get medicine-specific performance metrics"""
        # Top performing medicines (lowest MAPE)
        top_performers = forecasts.order_by('mape')[:10]
        
        # Worst performing medicines (highest MAPE)
        worst_performers = forecasts.order_by('-mape')[:10]
        
        # Medicines with most forecasts
        most_forecasted = forecasts.values('medicine__name').annotate(
            count=models.Count('id'),
            avg_mape=models.Avg('mape')
        ).order_by('-count')[:10]
        
        return {
            'top_performers': top_performers,
            'worst_performers': worst_performers,
            'most_forecasted': most_forecasted,
        }