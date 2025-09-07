from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class AuditLog(models.Model):
    """
    Comprehensive audit logging for all system activities
    """
    ACTION_TYPES = [
        ('create', 'Create'),
        ('read', 'Read'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('failed_login', 'Failed Login'),
        ('password_change', 'Password Change'),
        ('permission_change', 'Permission Change'),
        ('data_export', 'Data Export'),
        ('data_import', 'Data Import'),
        ('system_config', 'System Configuration'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Basic audit information
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')
    
    # Object being audited (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Action details
    description = models.TextField()
    old_values = models.JSONField(null=True, blank=True)  # previous state
    new_values = models.JSONField(null=True, blank=True)  # new state
    changed_fields = models.JSONField(null=True, blank=True)  # list of changed fields
    
    # Additional context
    module = models.CharField(max_length=50, blank=True)  # which app/module
    function_name = models.CharField(max_length=100, blank=True)
    request_path = models.CharField(max_length=200, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
    
    @property
    def is_high_risk(self):
        return self.severity in ['high', 'critical']


class SecurityEvent(models.Model):
    """
    Security-related events and incidents
    """
    EVENT_TYPES = [
        ('suspicious_login', 'Suspicious Login Attempt'),
        ('multiple_failed_logins', 'Multiple Failed Login Attempts'),
        ('unauthorized_access', 'Unauthorized Access Attempt'),
        ('data_breach_attempt', 'Data Breach Attempt'),
        ('privilege_escalation', 'Privilege Escalation Attempt'),
        ('sql_injection', 'SQL Injection Attempt'),
        ('xss_attempt', 'XSS Attempt'),
        ('csrf_attempt', 'CSRF Attempt'),
        ('file_upload_abuse', 'File Upload Abuse'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Event details
    description = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Request information
    request_path = models.CharField(max_length=200, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    
    # Response actions
    auto_blocked = models.BooleanField(default=False)
    manual_review_required = models.BooleanField(default=False)
    resolved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_security_events')
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional metadata
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['status', 'detected_at']),
            models.Index(fields=['ip_address', 'detected_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} - {self.detected_at}"


class SystemHealth(models.Model):
    """
    System health monitoring and metrics
    """
    METRIC_TYPES = [
        ('response_time', 'Response Time'),
        ('cpu_usage', 'CPU Usage'),
        ('memory_usage', 'Memory Usage'),
        ('disk_usage', 'Disk Usage'),
        ('database_connections', 'Database Connections'),
        ('active_users', 'Active Users'),
        ('error_rate', 'Error Rate'),
        ('throughput', 'Throughput'),
    ]
    
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.FloatField()
    unit = models.CharField(max_length=20)  # ms, %, MB, etc.
    
    # Context
    server_name = models.CharField(max_length=100, blank=True)
    environment = models.CharField(max_length=20, choices=[
        ('development', 'Development'),
        ('staging', 'Staging'),
        ('production', 'Production'),
    ], default='production')
    
    # Thresholds
    warning_threshold = models.FloatField(null=True, blank=True)
    critical_threshold = models.FloatField(null=True, blank=True)
    
    # Status
    is_healthy = models.BooleanField(default=True)
    alert_triggered = models.BooleanField(default=False)
    
    # Timestamps
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', 'recorded_at']),
            models.Index(fields=['is_healthy', 'recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.metric_type}: {self.value} {self.unit} at {self.recorded_at}"
    
    @property
    def status(self):
        if self.critical_threshold and self.value >= self.critical_threshold:
            return 'critical'
        elif self.warning_threshold and self.value >= self.warning_threshold:
            return 'warning'
        else:
            return 'healthy'


class ComplianceLog(models.Model):
    """
    Compliance and regulatory logging
    """
    COMPLIANCE_TYPES = [
        ('hipaa', 'HIPAA'),
        ('gdpr', 'GDPR'),
        ('pci_dss', 'PCI DSS'),
        ('sox', 'SOX'),
        ('fda', 'FDA'),
        ('pharmacy_board', 'Pharmacy Board'),
    ]
    
    compliance_type = models.CharField(max_length=20, choices=COMPLIANCE_TYPES)
    requirement = models.CharField(max_length=200)
    description = models.TextField()
    
    # Related objects
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Compliance status
    is_compliant = models.BooleanField(default=True)
    violation_severity = models.CharField(max_length=10, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], null=True, blank=True)
    
    # Action taken
    action_taken = models.TextField(blank=True)
    corrective_measures = models.TextField(blank=True)
    
    # Timestamps
    checked_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-checked_at']
        indexes = [
            models.Index(fields=['compliance_type', 'checked_at']),
            models.Index(fields=['is_compliant', 'checked_at']),
        ]
    
    def __str__(self):
        return f"{self.compliance_type} - {self.requirement} - {self.checked_at}"