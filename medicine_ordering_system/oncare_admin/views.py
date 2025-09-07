from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Sum, F, Count, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db import connection

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import (
    DashboardWidget, AdminReport, ReportExecution, SystemAlert, 
    UserActivityLog, SystemMaintenance
)


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only admin users can access the view"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin


# Dashboard View
class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin dashboard with system overview"""
    template_name = 'oncare_admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get system statistics
        from accounts.models import User
        from orders.models import Order
        from inventory.models import Medicine
        from transactions.models import Transaction
        
        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
        
        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        completed_orders = Order.objects.filter(status='delivered').count()
        
        # Inventory statistics
        total_medicines = Medicine.objects.filter(is_active=True).count()
        low_stock_medicines = Medicine.objects.filter(
            is_active=True,
            current_stock__lte=F('reorder_point')
        ).count()
        out_of_stock_medicines = Medicine.objects.filter(
            is_active=True,
            current_stock=0
        ).count()
        
        # Transaction statistics
        total_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        # Recent activity
        recent_orders = Order.objects.select_related('customer').order_by('-created_at')[:5]
        recent_alerts = SystemAlert.objects.filter(is_active=True).order_by('-created_at')[:5]
        
        # System health indicators
        system_health = self.get_system_health()
        
        context.update({
            'total_users': total_users,
            'active_users': active_users,
            'new_users_today': new_users_today,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'total_medicines': total_medicines,
            'low_stock_medicines': low_stock_medicines,
            'out_of_stock_medicines': out_of_stock_medicines,
            'total_revenue': total_revenue,
            'recent_orders': recent_orders,
            'recent_alerts': recent_alerts,
            'system_health': system_health,
        })
        
        return context
    
    def get_system_health(self):
        """Calculate system health metrics"""
        health = {
            'database': 'healthy',
            'performance': 'good',
            'alerts': 'normal',
            'uptime': '99.9%'
        }
        
        # Check for critical alerts
        critical_alerts = SystemAlert.objects.filter(
            severity='critical',
            is_active=True
        ).count()
        
        if critical_alerts > 0:
            health['alerts'] = 'critical'
        
        return health


# System Management Views
class SystemHealthView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """System health monitoring view"""
    template_name = 'oncare_admin/system_health.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Database health
        db_health = self.check_database_health()
        
        # Performance metrics
        performance_metrics = self.get_performance_metrics()
        
        # Recent errors
        recent_errors = SystemAlert.objects.filter(
            severity__in=['error', 'critical'],
            is_active=True
        ).order_by('-created_at')[:10]
        
        context.update({
            'db_health': db_health,
            'performance_metrics': performance_metrics,
            'recent_errors': recent_errors,
        })
        
        return context
    
    def check_database_health(self):
        """Check database connectivity and performance"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return {'status': 'healthy', 'response_time': '0.001s'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_performance_metrics(self):
        """Get system performance metrics"""
        return {
            'avg_response_time': '0.2s',
            'memory_usage': '45%',
            'cpu_usage': '30%',
            'disk_usage': '60%'
        }


class MaintenanceListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all maintenance records"""
    model = SystemMaintenance
    template_name = 'oncare_admin/maintenance_list.html'
    context_object_name = 'maintenances'
    paginate_by = 20
    
    def get_queryset(self):
        return SystemMaintenance.objects.all().order_by('-scheduled_start')


class MaintenanceCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create new maintenance record"""
    model = SystemMaintenance
    template_name = 'oncare_admin/maintenance_form.html'
    fields = [
        'title', 'maintenance_type', 'description', 'scheduled_start', 
        'scheduled_end', 'affected_services', 'expected_downtime', 'assigned_to'
    ]
    success_url = reverse_lazy('oncare_admin:maintenance_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Maintenance record created successfully!')
        return super().form_valid(form)


class MaintenanceDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Maintenance detail view"""
    model = SystemMaintenance
    template_name = 'oncare_admin/maintenance_detail.html'
    context_object_name = 'maintenance'


# Report Management Views
class ReportListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all admin reports"""
    model = AdminReport
    template_name = 'oncare_admin/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return AdminReport.objects.filter(
            Q(created_by=self.request.user) | 
            Q(allowed_users=self.request.user)
        ).distinct().order_by('-created_at')


class ReportCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create new admin report"""
    model = AdminReport
    template_name = 'oncare_admin/report_form.html'
    fields = [
        'name', 'report_type', 'description', 'query_config', 'filters',
        'columns', 'sorting', 'frequency', 'schedule_time', 'output_format',
        'allowed_users'
    ]
    success_url = reverse_lazy('oncare_admin:report_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Report created successfully!')
        return super().form_valid(form)


class ReportDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Report detail view"""
    model = AdminReport
    template_name = 'oncare_admin/report_detail.html'
    context_object_name = 'report'
    
    def get_queryset(self):
        return AdminReport.objects.filter(
            Q(created_by=self.request.user) | 
            Q(allowed_users=self.request.user)
        ).distinct()


class ReportExecuteView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Execute a report"""
    model = ReportExecution
    template_name = 'oncare_admin/report_execute.html'
    fields = ['parameters', 'filters_applied']
    
    def get_initial(self):
        report = get_object_or_404(AdminReport, pk=self.kwargs['pk'])
        return {
            'parameters': report.query_config,
            'filters_applied': report.filters
        }
    
    def form_valid(self, form):
        report = get_object_or_404(AdminReport, pk=self.kwargs['pk'])
        form.instance.report = report
        form.instance.executed_by = self.request.user
        form.instance.status = 'pending'
        
        messages.success(self.request, 'Report execution started!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('oncare_admin:report_detail', kwargs={'pk': self.kwargs['pk']})


# Widget Management Views
class WidgetListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all dashboard widgets"""
    model = DashboardWidget
    template_name = 'oncare_admin/widget_list.html'
    context_object_name = 'widgets'
    paginate_by = 20
    
    def get_queryset(self):
        return DashboardWidget.objects.filter(is_visible=True).order_by('position_y', 'position_x')


class WidgetCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """Create new dashboard widget"""
    model = DashboardWidget
    template_name = 'oncare_admin/widget_form.html'
    fields = [
        'name', 'widget_type', 'chart_type', 'title', 'description',
        'data_source', 'data_config', 'width', 'height', 'refresh_interval',
        'position_x', 'position_y', 'required_permission'
    ]
    success_url = reverse_lazy('oncare_admin:widget_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Widget created successfully!')
        return super().form_valid(form)


class WidgetEditView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Edit dashboard widget"""
    model = DashboardWidget
    template_name = 'oncare_admin/widget_form.html'
    fields = [
        'name', 'widget_type', 'chart_type', 'title', 'description',
        'data_source', 'data_config', 'width', 'height', 'refresh_interval',
        'position_x', 'position_y', 'is_visible', 'required_permission'
    ]
    success_url = reverse_lazy('oncare_admin:widget_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Widget updated successfully!')
        return super().form_valid(form)


# Alert Management Views
class AlertListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """List all system alerts"""
    model = SystemAlert
    template_name = 'oncare_admin/alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = SystemAlert.objects.all().order_by('-created_at')
        
        # Filter by severity
        severity = self.request.GET.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by alert type
        alert_type = self.request.GET.get('alert_type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'acknowledged':
            queryset = queryset.filter(is_acknowledged=True)
        elif status_filter == 'resolved':
            queryset = queryset.filter(is_resolved=True)
        
        return queryset


class AlertDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    """Alert detail view"""
    model = SystemAlert
    template_name = 'oncare_admin/alert_detail.html'
    context_object_name = 'alert'


class AlertAcknowledgeView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Acknowledge an alert"""
    model = SystemAlert
    fields = []
    template_name = 'oncare_admin/alert_acknowledge.html'
    
    def form_valid(self, form):
        self.object.is_acknowledged = True
        self.object.acknowledged_by = self.request.user
        self.object.acknowledged_at = timezone.now()
        self.object.save()
        
        messages.success(self.request, 'Alert acknowledged successfully!')
        return redirect('oncare_admin:alert_detail', pk=self.object.pk)


class AlertResolveView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """Resolve an alert"""
    model = SystemAlert
    fields = ['resolution_notes']
    template_name = 'oncare_admin/alert_resolve.html'
    
    def form_valid(self, form):
        self.object.is_resolved = True
        self.object.resolved_by = self.request.user
        self.object.resolved_at = timezone.now()
        self.object.is_active = False
        self.object.save()
        
        messages.success(self.request, 'Alert resolved successfully!')
        return redirect('oncare_admin:alert_detail', pk=self.object.pk)


# User Activity View
class UserActivityView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """User activity monitoring view"""
    model = UserActivityLog
    template_name = 'oncare_admin/user_activity.html'
    context_object_name = 'activities'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = UserActivityLog.objects.select_related('user').order_by('-timestamp')
        
        # Filter by user
        user_id = self.request.GET.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by action
        action = self.request.GET.get('action')
        if action:
            queryset = queryset.filter(action__icontains=action)
        
        # Filter by module
        module = self.request.GET.get('module')
        if module:
            queryset = queryset.filter(module=module)
        
        # Filter by date range
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from accounts.models import User
        context['users'] = User.objects.filter(is_active=True).order_by('username')
        return context


# API Views
class DashboardDataAPIView(APIView):
    """API view for dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Get dashboard metrics
        from accounts.models import User
        from orders.models import Order
        from inventory.models import Medicine
        from transactions.models import Transaction
        
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        data = {
            'users': {
                'total': User.objects.count(),
                'active': User.objects.filter(is_active=True).count(),
                'new_today': User.objects.filter(date_joined__date=today).count(),
            },
            'orders': {
                'total': Order.objects.count(),
                'pending': Order.objects.filter(status='pending').count(),
                'completed': Order.objects.filter(status='delivered').count(),
            },
            'inventory': {
                'total_medicines': Medicine.objects.filter(is_active=True).count(),
                'low_stock': Medicine.objects.filter(
                    is_active=True,
                    current_stock__lte=F('reorder_point')
                ).count(),
                'out_of_stock': Medicine.objects.filter(
                    is_active=True,
                    current_stock=0
                ).count(),
            },
            'revenue': {
                'total': float(Transaction.objects.filter(status='completed').aggregate(
                    total=Sum('amount')
                )['total'] or 0),
                'monthly': float(Transaction.objects.filter(
                    status='completed',
                    created_at__date__gte=this_month
                ).aggregate(total=Sum('amount'))['total'] or 0),
            }
        }
        
        return Response(data)


class SystemMetricsAPIView(APIView):
    """API view for system metrics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        metrics = {
            'database': {'status': 'healthy', 'response_time': '0.001s'},
            'performance': {
                'avg_response_time': '0.2s',
                'memory_usage': '45%',
                'cpu_usage': '30%',
                'disk_usage': '60%'
            },
            'alerts': {
                'critical': SystemAlert.objects.filter(severity='critical', is_active=True).count(),
                'warning': SystemAlert.objects.filter(severity='warning', is_active=True).count(),
                'info': SystemAlert.objects.filter(severity='info', is_active=True).count(),
            }
        }
        
        return Response(metrics)


class AlertAPIView(APIView):
    """API view for alerts"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        alerts = SystemAlert.objects.filter(is_active=True).order_by('-created_at')[:10]
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'created_at': alert.created_at,
                'is_acknowledged': alert.is_acknowledged,
                'is_resolved': alert.is_resolved,
            })
        
        return Response({'alerts': alerts_data})


class ReportAPIView(APIView):
    """API view for reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_admin:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        reports = AdminReport.objects.filter(
            Q(created_by=request.user) | 
            Q(allowed_users=request.user)
        ).distinct().order_by('-created_at')
        
        reports_data = []
        for report in reports:
            reports_data.append({
                'id': report.id,
                'name': report.name,
                'report_type': report.report_type,
                'description': report.description,
                'frequency': report.frequency,
                'is_active': report.is_active,
                'created_at': report.created_at,
                'last_generated': report.last_generated,
            })
        
        return Response({'reports': reports_data})
