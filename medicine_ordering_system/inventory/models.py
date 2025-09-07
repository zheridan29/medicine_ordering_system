from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Category(models.Model):
    """
    Medicine categories for better organization
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """
    Medicine manufacturers
    """
    name = models.CharField(max_length=200, unique=True)
    country = models.CharField(max_length=100)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    """
    Medicine catalog with detailed information
    """
    PRESCRIPTION_CHOICES = [
        ('prescription', 'Prescription Required'),
        ('otc', 'Over the Counter'),
        ('controlled', 'Controlled Substance'),
    ]
    
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='medicines')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, related_name='medicines')
    
    # Medicine details
    dosage_form = models.CharField(max_length=50)  # tablet, capsule, syrup, etc.
    strength = models.CharField(max_length=50)  # 500mg, 10ml, etc.
    prescription_type = models.CharField(max_length=20, choices=PRESCRIPTION_CHOICES, default='otc')
    
    # Pricing
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Inventory
    current_stock = models.PositiveIntegerField(default=0)
    minimum_stock_level = models.PositiveIntegerField(default=10)
    maximum_stock_level = models.PositiveIntegerField(default=1000)
    reorder_point = models.PositiveIntegerField(default=20)
    
    # Physical attributes
    weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)  # in grams
    dimensions = models.CharField(max_length=100, blank=True)  # LxWxH
    storage_conditions = models.CharField(max_length=200, blank=True)
    
    # Regulatory
    ndc_number = models.CharField(max_length=20, unique=True, blank=True)  # National Drug Code
    fda_approval_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    requires_prescription = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active', 'is_available']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_point
    
    @property
    def is_out_of_stock(self):
        return self.current_stock == 0
    
    @property
    def stock_status(self):
        if self.is_out_of_stock:
            return "Out of Stock"
        elif self.is_low_stock:
            return "Low Stock"
        else:
            return "In Stock"


class StockMovement(models.Model):
    """
    Track all stock movements (in/out)
    """
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Stock Adjustment'),
        ('return', 'Return'),
        ('damage', 'Damaged'),
        ('expired', 'Expired'),
    ]
    
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='stock_movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()  # positive for in, negative for out
    reference_number = models.CharField(max_length=50, blank=True)  # PO number, invoice number, etc.
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.medicine.name} - {self.quantity}"


class ReorderAlert(models.Model):
    """
    Alerts for medicines that need reordering
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='reorder_alerts')
    current_stock = models.PositiveIntegerField()
    reorder_point = models.PositiveIntegerField()
    suggested_quantity = models.PositiveIntegerField()
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], default='medium')
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"Reorder Alert: {self.medicine.name}"


class MedicineImage(models.Model):
    """
    Images for medicines
    """
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='medicine_images/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.medicine.name}"