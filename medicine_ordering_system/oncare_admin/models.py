from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class DashboardWidget(models.Model):
    """
    Configurable dashboard widgets for admin users
    """
    WIDGET_TYPES = [
        ('chart', 'Chart'),
        ('metric', 'Metric'),
        ('table', 'Table'),
        ('alert', 'Alert'),
        ('map', 'Map'),
    ]
    
    CHART_TYPES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('doughnut', 'Doughnut Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
    ]
    
    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES, blank=True)
    
    # Configuration
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    data_source = models.CharField(max_length=100)  # which model/query to use
    data_config = models.JSONField(default=dict)  # configuration for data retrieval
    
    # Display settings
    width = models.PositiveIntegerField(default=4)  # Bootstrap grid width (1-12)
    height = models.PositiveIntegerField(default=300)  # height in pixels
    refresh_interval = models.PositiveIntegerField(default=300)  # seconds
    
    # Position and visibility
    position_x = models.PositiveIntegerField(default=0)
    position_y = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    
    # Access control
    required_permission = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.name} ({self.widget_type})"


class AdminReport(models.Model):
    """
    Custom reports for admin users
    """
    REPORT_TYPES = [
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('customer', 'Customer Report'),
        ('financial', 'Financial Report'),
        ('operational', 'Operational Report'),
        ('compliance', 'Compliance Report'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('on_demand', 'On Demand'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Configuration
    query_config = models.JSONField(default=dict)  # configuration for data retrieval
    filters = models.JSONField(default=dict)  # available filters
    columns = models.JSONField(default=list)  # columns to display
    sorting = models.JSONField(default=dict)  # default sorting
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='on_demand')
    schedule_time = models.TimeField(null=True, blank=True)  # for scheduled reports
    is_active = models.BooleanField(default=True)
    
    # Access control
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='created_reports')
    allowed_users = models.ManyToManyField('accounts.User', related_name='accessible_reports', blank=True)
    required_permission = models.CharField(max_length=100, blank=True)
    
    # Output settings
    output_format = models.CharField(max_length=20, choices=[
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('html', 'HTML'),
    ], default='pdf')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.report_type})"


class ReportExecution(models.Model):
    """
    Track report executions and results
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    report = models.ForeignKey(AdminReport, on_delete=models.CASCADE, related_name='executions')
    executed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    
    # Execution details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parameters = models.JSONField(default=dict)  # parameters used for this execution
    filters_applied = models.JSONField(default=dict)
    
    # Results
    file_path = models.CharField(max_length=500, blank=True)
    file_size = models.PositiveIntegerField(null=True, blank=True)
    record_count = models.PositiveIntegerField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True)
    error_details = models.JSONField(null=True, blank=True)
    
    # Performance metrics
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    memory_used = models.PositiveIntegerField(null=True, blank=True)  # in MB
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.report.name} - {self.status} - {self.started_at}"


class SystemAlert(models.Model):
    """
    System alerts and notifications for admin users
    """
    ALERT_TYPES = [
        ('inventory', 'Inventory Alert'),
        ('order', 'Order Alert'),
        ('payment', 'Payment Alert'),
        ('security', 'Security Alert'),
        ('system', 'System Alert'),
        ('compliance', 'Compliance Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Alert content
    title = models.CharField(max_length=200)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    # Related objects
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'is_active']),
            models.Index(fields=['severity', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.title}"


class UserActivityLog(models.Model):
    """
    Detailed user activity logging for admin monitoring
    """
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='activity_logs')
    
    # Activity details
    action = models.CharField(max_length=100)
    description = models.TextField()
    module = models.CharField(max_length=50)
    
    # Request information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=200, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    duration = models.FloatField(null=True, blank=True)  # in seconds
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['module', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"


class SystemMaintenance(models.Model):
    """
    System maintenance scheduling and tracking
    """
    MAINTENANCE_TYPES = [
        ('scheduled', 'Scheduled Maintenance'),
        ('emergency', 'Emergency Maintenance'),
        ('update', 'System Update'),
        ('backup', 'Backup'),
        ('security', 'Security Patch'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    title = models.CharField(max_length=200)
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPES)
    description = models.TextField()
    
    # Scheduling
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)
    
    # Status and progress
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    progress_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    
    # Impact
    affected_services = models.JSONField(default=list, blank=True)
    expected_downtime = models.DurationField(null=True, blank=True)
    user_notification_sent = models.BooleanField(default=False)
    
    # Personnel
    assigned_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_maintenance')
    
    # Results
    notes = models.TextField(blank=True)
    issues_encountered = models.TextField(blank=True)
    post_maintenance_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_start']
    
    def __str__(self):
        return f"{self.title} - {self.scheduled_start}"
    
    @property
    def duration(self):
        if self.actual_start and self.actual_end:
            return self.actual_end - self.actual_start
        elif self.actual_start:
            from django.utils import timezone
            return timezone.now() - self.actual_start
        else:
            return self.scheduled_end - self.scheduled_start