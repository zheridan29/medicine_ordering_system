from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta

# Import models from different apps
from accounts.models import User
from orders.models import Order
from inventory.models import Medicine, StockMovement
from transactions.models import Transaction
from analytics.models import SystemMetrics

class HomeView(LoginRequiredMixin, TemplateView):
    """Home page view that redirects users based on their role"""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get basic statistics
        context['user'] = user
        context['current_time'] = timezone.now()
        
        # Role-specific data
        if user.is_admin:
            context.update(self.get_admin_context())
        elif user.is_pharmacist_admin:
            context.update(self.get_pharmacist_admin_context())
        else:  # Sales Representative
            context.update(self.get_sales_rep_context())
            
        return context
    
    def get_admin_context(self):
        """Admin-specific dashboard data"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        return {
            'total_users': User.objects.count(),
            'total_orders': Order.objects.count(),
            'total_medicines': Medicine.objects.count(),
            'recent_orders': Order.objects.filter(created_at__date=today).count(),
            'weekly_orders': Order.objects.filter(created_at__date__gte=week_ago).count(),
            'monthly_orders': Order.objects.filter(created_at__date__gte=month_ago).count(),
            'total_revenue': Transaction.objects.aggregate(total=Sum('amount'))['total'] or 0,
            'low_stock_medicines': Medicine.objects.filter(stock_quantity__lt=10).count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
        }
    
    def get_pharmacist_admin_context(self):
        """Pharmacist/Admin-specific dashboard data - shows all orders from sales reps"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        return {
            'total_medicines': Medicine.objects.count(),
            'low_stock_medicines': Medicine.objects.filter(current_stock__lt=10).count(),
            'recent_orders': Order.objects.filter(created_at__date=today).count(),
            'weekly_orders': Order.objects.filter(created_at__date__gte=week_ago).count(),
            'pending_orders': Order.objects.filter(status='pending').count(),
            'recent_stock_movements': StockMovement.objects.filter(created_at__date=today).count(),
            'all_orders': Order.objects.count(),  # All orders from sales reps
            'today_orders': Order.objects.filter(created_at__date=today).count(),
            'pending_orders_count': Order.objects.filter(status='pending').count(),
        }
    
    def get_sales_rep_context(self):
        """Sales Representative-specific dashboard data"""
        user = self.request.user
        today = timezone.now().date()
        
        return {
            'user_orders': Order.objects.filter(sales_rep=user).count(),
            'recent_orders': Order.objects.filter(sales_rep=user, created_at__date=today).count(),
            'pending_orders': Order.objects.filter(sales_rep=user, status='pending').count(),
            'completed_orders': Order.objects.filter(sales_rep=user, status='delivered').count(),
        }



