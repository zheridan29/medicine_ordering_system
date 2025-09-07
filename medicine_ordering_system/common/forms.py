from django import forms
from .models import Notification, SystemConfiguration, FileUpload, EmailTemplate, Address

class NotificationForm(forms.ModelForm):
    """Form for creating and editing notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'user', 'notification_type', 'priority', 'title', 'message',
            'action_url', 'expires_at', 'email_sent', 'sms_sent', 'push_sent'
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'action_url': forms.URLInput(attrs={'class': 'form-control'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'email_sent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_sent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_sent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class SystemConfigurationForm(forms.ModelForm):
    """Form for editing system configuration"""
    
    class Meta:
        model = SystemConfiguration
        fields = ['key', 'value', 'config_type', 'description', 'data_type', 'is_required']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'value': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'config_type': forms.Select(attrs={'class': 'form-select', 'readonly': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'data_type': forms.Select(attrs={'class': 'form-select', 'readonly': True}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input', 'disabled': True}),
        }

class FileUploadForm(forms.ModelForm):
    """Form for uploading files"""
    
    class Meta:
        model = FileUpload
        fields = ['file_type', 'file', 'access_level', 'instructions']
        widgets = {
            'file_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'access_level': forms.Select(attrs={'class': 'form-select'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EmailTemplateForm(forms.ModelForm):
    """Form for creating and editing email templates"""
    
    class Meta:
        model = EmailTemplate
        fields = [
            'name', 'template_type', 'subject', 'html_content', 'text_content',
            'available_variables', 'is_active', 'is_default'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'html_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'text_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'available_variables': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AddressForm(forms.ModelForm):
    """Form for creating and editing addresses"""
    
    class Meta:
        model = Address
        fields = [
            'address_type', 'line1', 'line2', 'city', 'state', 'zip_code',
            'country', 'contact_name', 'phone_number', 'instructions', 'is_default'
        ]
        widgets = {
            'address_type': forms.Select(attrs={'class': 'form-select'}),
            'line1': forms.TextInput(attrs={'class': 'form-control'}),
            'line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



