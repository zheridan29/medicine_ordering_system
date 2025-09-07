from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Notification, SystemConfiguration, FileUpload, EmailTemplate

# Create your views here.

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "common/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(user=self.request.user)
        # Filter by read status
        is_read = self.request.GET.get('is_read')
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        # Filter by notification type
        notification_type = self.request.GET.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        return queryset

class NotificationDetailView(LoginRequiredMixin, DetailView):
    model = Notification
    template_name = "common/notification_detail.html"
    context_object_name = "notification"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})

class ConfigurationListView(LoginRequiredMixin, ListView):
    model = SystemConfiguration
    template_name = "common/configuration_list.html"
    context_object_name = "configurations"
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by config type
        config_type = self.request.GET.get('config_type')
        if config_type:
            queryset = queryset.filter(config_type=config_type)
        return queryset

class ConfigurationEditView(LoginRequiredMixin, UpdateView):
    model = SystemConfiguration
    fields = ['value', 'description']
    template_name = "common/configuration_edit.html"
    context_object_name = "configuration"
    success_url = reverse_lazy('common:config_list')

class FileUploadListView(LoginRequiredMixin, ListView):
    model = FileUpload
    template_name = "common/file_upload_list.html"
    context_object_name = "file_uploads"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(uploaded_by=self.request.user)
        # Filter by file type
        file_type = self.request.GET.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        return queryset

class FileUploadDetailView(LoginRequiredMixin, DetailView):
    model = FileUpload
    template_name = "common/file_upload_detail.html"
    context_object_name = "file_upload"

    def get_queryset(self):
        return super().get_queryset().filter(uploaded_by=self.request.user)

class EmailTemplateListView(LoginRequiredMixin, ListView):
    model = EmailTemplate
    template_name = "common/email_template_list.html"
    context_object_name = "email_templates"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by template type
        template_type = self.request.GET.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        return queryset

class EmailTemplateCreateView(LoginRequiredMixin, CreateView):
    model = EmailTemplate
    fields = ['name', 'template_type', 'subject', 'html_content', 'text_content', 'available_variables', 'is_active']
    template_name = "common/email_template_create.html"
    success_url = reverse_lazy('common:email_template_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class EmailTemplateEditView(LoginRequiredMixin, UpdateView):
    model = EmailTemplate
    fields = ['name', 'template_type', 'subject', 'html_content', 'text_content', 'available_variables', 'is_active']
    template_name = "common/email_template_edit.html"
    context_object_name = "email_template"
    success_url = reverse_lazy('common:email_template_list')

# API Views
class NotificationAPIView(LoginRequiredMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)[:50]
        data = []
        for notification in notifications:
            data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'priority': notification.priority,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'action_url': notification.action_url,
            })
        return JsonResponse({'notifications': data})

class ConfigurationAPIView(LoginRequiredMixin, View):
    def get(self, request):
        configs = SystemConfiguration.objects.all()
        data = {}
        for config in configs:
            data[config.key] = {
                'value': config.get_typed_value(),
                'config_type': config.config_type,
                'description': config.description,
                'data_type': config.data_type,
            }
        return JsonResponse({'configurations': data})

class FileUploadAPIView(LoginRequiredMixin, View):
    def get(self, request):
        uploads = FileUpload.objects.filter(uploaded_by=request.user)[:50]
        data = []
        for upload in uploads:
            data.append({
                'id': upload.id,
                'file_type': upload.file_type,
                'original_filename': upload.original_filename,
                'file_size': upload.file_size,
                'file_size_mb': upload.file_size_mb,
                'mime_type': upload.mime_type,
                'is_processed': upload.is_processed,
                'processing_status': upload.processing_status,
                'uploaded_at': upload.uploaded_at.isoformat(),
            })
        return JsonResponse({'file_uploads': data})
