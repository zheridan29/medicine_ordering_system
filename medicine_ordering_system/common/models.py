from django.db import models
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class BaseModel(models.Model):
    """
    Abstract base model with common fields
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        abstract = True


class Address(models.Model):
    """
    Reusable address model
    """
    ADDRESS_TYPES = [
        ('billing', 'Billing Address'),
        ('shipping', 'Shipping Address'),
        ('business', 'Business Address'),
    ]
    
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='shipping')
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='USA')
    
    # Contact information
    contact_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'.")],
        blank=True
    )
    
    # Additional details
    instructions = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_default', 'created_at']
    
    def __str__(self):
        return f"{self.line1}, {self.city}, {self.state} {self.zip_code}"


class Notification(models.Model):
    """
    System notifications for users
    """
    NOTIFICATION_TYPES = [
        ('order_update', 'Order Update'),
        ('stock_alert', 'Stock Alert'),
        ('prescription_ready', 'Prescription Ready'),
        ('payment_confirmation', 'Payment Confirmation'),
        ('system_maintenance', 'System Maintenance'),
        ('promotion', 'Promotion'),
        ('security_alert', 'Security Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Content
    title = models.CharField(max_length=200)
    message = models.TextField()
    action_url = models.URLField(blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Delivery methods
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    push_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings
    """
    CONFIG_TYPES = [
        ('general', 'General'),
        ('inventory', 'Inventory'),
        ('orders', 'Orders'),
        ('payments', 'Payments'),
        ('notifications', 'Notifications'),
        ('security', 'Security'),
        ('analytics', 'Analytics'),
    ]
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, default='general')
    description = models.TextField(blank=True)
    
    # Data type information
    data_type = models.CharField(max_length=20, choices=[
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ], default='string')
    
    # Validation
    is_required = models.BooleanField(default=False)
    validation_regex = models.CharField(max_length=200, blank=True)
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['config_type', 'key']
    
    def __str__(self):
        return f"{self.key} = {self.value}"
    
    def get_typed_value(self):
        """Return the value converted to its proper data type"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes', 'on')
        elif self.data_type == 'json':
            import json
            return json.loads(self.value)
        else:
            return self.value


class FileUpload(models.Model):
    """
    Generic file upload model
    """
    FILE_TYPES = [
        ('prescription', 'Prescription'),
        ('insurance', 'Insurance Card'),
        ('id', 'ID Document'),
        ('medical_record', 'Medical Record'),
        ('invoice', 'Invoice'),
        ('report', 'Report'),
        ('other', 'Other'),
    ]
    
    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file = models.FileField(upload_to='uploads/')
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()  # in bytes
    mime_type = models.CharField(max_length=100)
    
    # Related objects
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # File processing
    is_processed = models.BooleanField(default=False)
    processing_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    processing_notes = models.TextField(blank=True)
    
    # Security
    is_encrypted = models.BooleanField(default=False)
    access_level = models.CharField(max_length=20, choices=[
        ('public', 'Public'),
        ('private', 'Private'),
        ('confidential', 'Confidential'),
    ], default='private')
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['file_type', 'uploaded_at']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.file_type})"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)


class EmailTemplate(models.Model):
    """
    Email templates for various notifications
    """
    TEMPLATE_TYPES = [
        ('welcome', 'Welcome Email'),
        ('order_confirmation', 'Order Confirmation'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('prescription_ready', 'Prescription Ready'),
        ('payment_confirmation', 'Payment Confirmation'),
        ('password_reset', 'Password Reset'),
        ('account_verification', 'Account Verification'),
        ('stock_alert', 'Stock Alert'),
        ('promotion', 'Promotion'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    html_content = models.TextField()
    text_content = models.TextField(blank=True)
    
    # Template variables
    available_variables = models.JSONField(default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['template_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"