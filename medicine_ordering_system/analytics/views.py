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