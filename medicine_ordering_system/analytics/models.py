from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class DemandForecast(models.Model):
    """
    ARIMA-based demand forecasting results
    """
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.CASCADE, related_name='demand_forecasts')
    
    # Forecast parameters
    forecast_period = models.CharField(max_length=20, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='weekly')
    forecast_horizon = models.PositiveIntegerField(default=4)  # number of periods to forecast
    
    # ARIMA model parameters
    arima_p = models.PositiveIntegerField()  # autoregressive order
    arima_d = models.PositiveIntegerField()  # differencing order
    arima_q = models.PositiveIntegerField()  # moving average order
    
    # Model evaluation metrics
    aic = models.FloatField()  # Akaike Information Criterion
    bic = models.FloatField()  # Bayesian Information Criterion
    rmse = models.FloatField()  # Root Mean Square Error
    mae = models.FloatField()   # Mean Absolute Error
    mape = models.FloatField()  # Mean Absolute Percentage Error
    
    # Forecast results
    forecasted_demand = models.JSONField()  # array of forecasted values
    confidence_intervals = models.JSONField()  # upper and lower bounds
    
    # Historical data used for training
    training_data_start = models.DateField()
    training_data_end = models.DateField()
    training_data_points = models.PositiveIntegerField()
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['medicine', 'forecast_period']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Demand Forecast for {self.medicine.name} - {self.forecast_period}"
    
    @property
    def model_quality(self):
        """Determine model quality based on metrics"""
        if self.mape < 10:
            return "Excellent"
        elif self.mape < 20:
            return "Good"
        elif self.mape < 30:
            return "Fair"
        else:
            return "Poor"


class InventoryOptimization(models.Model):
    """
    Optimal inventory levels based on demand forecasting
    """
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.CASCADE, related_name='inventory_optimizations')
    demand_forecast = models.ForeignKey(DemandForecast, on_delete=models.CASCADE, related_name='optimizations')
    
    # Optimization parameters
    service_level = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('99.99'))],
        default=Decimal('95.00')
    )  # desired service level percentage
    lead_time_days = models.PositiveIntegerField(default=7)
    holding_cost_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    
    # Calculated optimal levels
    optimal_reorder_point = models.PositiveIntegerField()
    optimal_order_quantity = models.PositiveIntegerField()
    optimal_maximum_stock = models.PositiveIntegerField()
    safety_stock = models.PositiveIntegerField()
    
    # Cost analysis
    expected_holding_cost = models.DecimalField(max_digits=10, decimal_places=2)
    expected_stockout_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_expected_cost = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    calculated_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"Inventory Optimization for {self.medicine.name}"


class SalesTrend(models.Model):
    """
    Historical sales trends and patterns
    """
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.CASCADE, related_name='sales_trends')
    
    # Time period
    period_type = models.CharField(max_length=10, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    period_date = models.DateField()
    
    # Sales metrics
    quantity_sold = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Trend indicators
    growth_rate = models.FloatField(null=True, blank=True)  # percentage change from previous period
    seasonal_factor = models.FloatField(null=True, blank=True)  # seasonal adjustment factor
    trend_direction = models.CharField(max_length=10, choices=[
        ('up', 'Upward'),
        ('down', 'Downward'),
        ('stable', 'Stable'),
    ], null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['medicine', 'period_type', 'period_date']
        ordering = ['-period_date']
        indexes = [
            models.Index(fields=['medicine', 'period_type', 'period_date']),
        ]
    
    def __str__(self):
        return f"Sales Trend - {self.medicine.name} - {self.period_date}"


class CustomerAnalytics(models.Model):
    """
    Customer behavior and analytics
    """
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='analytics')
    
    # Purchase behavior
    total_orders = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Frequency metrics
    days_since_last_order = models.PositiveIntegerField(null=True, blank=True)
    order_frequency_days = models.PositiveIntegerField(null=True, blank=True)  # average days between orders
    
    # Customer segmentation
    customer_segment = models.CharField(max_length=20, choices=[
        ('new', 'New Customer'),
        ('regular', 'Regular Customer'),
        ('vip', 'VIP Customer'),
        ('at_risk', 'At Risk'),
        ('inactive', 'Inactive'),
    ], default='new')
    
    # Preferences
    preferred_categories = models.JSONField(default=list)  # list of category IDs
    preferred_payment_method = models.CharField(max_length=50, blank=True)
    
    # Risk indicators
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    complaint_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"Analytics for {self.customer.username}"


class SystemMetrics(models.Model):
    """
    System-wide performance and business metrics
    """
    # Time period
    period_type = models.CharField(max_length=10, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    period_date = models.DateField()
    
    # Business metrics
    total_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_customers = models.PositiveIntegerField(default=0)
    new_customers = models.PositiveIntegerField(default=0)
    
    # Inventory metrics
    total_medicines = models.PositiveIntegerField(default=0)
    low_stock_items = models.PositiveIntegerField(default=0)
    out_of_stock_items = models.PositiveIntegerField(default=0)
    inventory_turnover = models.FloatField(default=0.0)
    
    # Performance metrics
    average_order_processing_time = models.FloatField(default=0.0)  # in hours
    customer_satisfaction_score = models.FloatField(null=True, blank=True)
    prescription_verification_time = models.FloatField(default=0.0)  # in hours
    
    # System health
    system_uptime = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    error_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['period_type', 'period_date']
        ordering = ['-period_date']
    
    def __str__(self):
        return f"System Metrics - {self.period_type} - {self.period_date}"