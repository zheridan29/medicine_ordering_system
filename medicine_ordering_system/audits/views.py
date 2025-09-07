from django.shortcuts import render
from django.views.generic import TemplateView, ListView, DetailView
from .models import AuditLog, SecurityEvent, SystemHealth, ComplianceLog  # Add missing model imports
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.http import JsonResponse
from django.views import View
from django.db.models import Avg, Count, Q
from datetime import datetime, timedelta

class AuditDashboardView(TemplateView):
    template_name = "audits/dashboard.html"
    # You can add context data if needed
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # Add custom context here
    #     return context

class AuditLogListView(ListView):
    model = AuditLog
    template_name = "audits/auditlog_list.html"
    context_object_name = "audit_logs"
    # ...existing code...

class AuditLogDetailView(DetailView):
    model = AuditLog
    template_name = "audits/auditlog_detail.html"
    context_object_name = "audit_log"
    # ...existing code...

class SecurityEventListView(ListView):
    model = SecurityEvent
    template_name = "audits/securityevent_list.html"
    context_object_name = "security_events"
    # ...existing code...

class SecurityEventDetailView(DetailView):
    model = SecurityEvent
    template_name = "audits/securityevent_detail.html"
    context_object_name = "security_event"
    # ...existing code...

class SecurityEventResolveView(UpdateView):
    model = SecurityEvent
    fields = ['status', 'resolved_by', 'resolution_notes', 'resolved_at']  # Use model fields for resolving
    template_name = "audits/securityevent_resolve.html"
    context_object_name = "security_event"
    success_url = reverse_lazy('audits:security_event_list')  # Use correct URL name

class SystemHealthListView(ListView):
    model = SystemHealth
    template_name = "audits/systemhealth_list.html"
    context_object_name = "system_health_metrics"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by metric type if provided
        metric_type = self.request.GET.get('metric_type')
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        return queryset

class SystemHealthMetricsView(TemplateView):
    template_name = "audits/systemhealth_metrics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get recent metrics (last 24 hours)
        recent_metrics = SystemHealth.objects.filter(
            recorded_at__gte=datetime.now() - timedelta(days=1)
        )
        
        # Group by metric type and get latest values
        metrics_by_type = {}
        for metric in recent_metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            metrics_by_type[metric.metric_type].append(metric)
        
        # Get latest value for each metric type
        latest_metrics = {}
        for metric_type, metrics in metrics_by_type.items():
            latest_metrics[metric_type] = max(metrics, key=lambda x: x.recorded_at)
        
        context['latest_metrics'] = latest_metrics
        context['unhealthy_metrics'] = SystemHealth.objects.filter(
            is_healthy=False,
            recorded_at__gte=datetime.now() - timedelta(hours=1)
        )
        
        return context

class ComplianceLogListView(ListView):
    model = ComplianceLog
    template_name = "audits/compliancelog_list.html"
    context_object_name = "compliance_logs"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by compliance type if provided
        compliance_type = self.request.GET.get('compliance_type')
        if compliance_type:
            queryset = queryset.filter(compliance_type=compliance_type)
        # Filter by compliance status if provided
        is_compliant = self.request.GET.get('is_compliant')
        if is_compliant is not None:
            queryset = queryset.filter(is_compliant=is_compliant.lower() == 'true')
        return queryset

class ComplianceLogDetailView(DetailView):
    model = ComplianceLog
    template_name = "audits/compliancelog_detail.html"
    context_object_name = "compliance_log"

# API Views
class AuditLogAPIView(View):
    def get(self, request):
        logs = AuditLog.objects.all()[:100]  # Limit to 100 recent logs
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'user': log.user.username if log.user else 'Anonymous',
                'action': log.action,
                'severity': log.severity,
                'description': log.description,
                'timestamp': log.timestamp.isoformat(),
                'ip_address': str(log.ip_address),
            })
        return JsonResponse({'audit_logs': data})

class SecurityEventAPIView(View):
    def get(self, request):
        events = SecurityEvent.objects.all()[:100]  # Limit to 100 recent events
        data = []
        for event in events:
            data.append({
                'id': event.id,
                'event_type': event.event_type,
                'severity': event.severity,
                'status': event.status,
                'description': event.description,
                'detected_at': event.detected_at.isoformat(),
                'ip_address': str(event.ip_address),
                'auto_blocked': event.auto_blocked,
            })
        return JsonResponse({'security_events': data})

class SystemHealthAPIView(View):
    def get(self, request):
        # Get latest metrics for each type
        latest_metrics = {}
        for metric_type, _ in SystemHealth.METRIC_TYPES:
            latest = SystemHealth.objects.filter(metric_type=metric_type).first()
            if latest:
                latest_metrics[metric_type] = {
                    'value': latest.value,
                    'unit': latest.unit,
                    'is_healthy': latest.is_healthy,
                    'status': latest.status,
                    'recorded_at': latest.recorded_at.isoformat(),
                }
        
        return JsonResponse({'system_health': latest_metrics})

class ComplianceAPIView(View):
    def get(self, request):
        logs = ComplianceLog.objects.all()[:100]  # Limit to 100 recent logs
        data = []
        for log in logs:
            data.append({
                'id': log.id,
                'compliance_type': log.compliance_type,
                'requirement': log.requirement,
                'is_compliant': log.is_compliant,
                'violation_severity': log.violation_severity,
                'checked_at': log.checked_at.isoformat(),
            })
        return JsonResponse({'compliance_logs': data})

# Create your views here.
