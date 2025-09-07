from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal


class Order(models.Model):
    """
    Customer orders
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True)
    sales_rep = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sales_orders', null=True, blank=True)
    customer_name = models.CharField(max_length=100, default='')
    customer_phone = models.CharField(max_length=15, default='')
    customer_address = models.TextField(default='')
    
    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Delivery information
    delivery_method = models.CharField(max_length=20, choices=[
        ('pickup', 'Store Pickup'),
        ('delivery', 'Home Delivery'),
    ], default='pickup')
    delivery_address = models.TextField(blank=True)
    delivery_instructions = models.TextField(blank=True)
    
    # Prescription information
    prescription_required = models.BooleanField(default=False)
    prescription_image = models.ImageField(upload_to='prescriptions/', blank=True, null=True)
    prescription_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_prescriptions')
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Notes
    customer_notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['sales_rep', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        import uuid
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    @property
    def is_prescription_order(self):
        return self.prescription_required and self.prescription_image
    
    def decrease_stock(self):
        """Decrease stock for all items in this order"""
        from inventory.models import StockMovement
        from django.utils import timezone
        
        for item in self.items.all():
            # Decrease the medicine's current stock
            item.medicine.current_stock -= item.quantity
            item.medicine.save()
            
            # Create stock movement record
            StockMovement.objects.create(
                medicine=item.medicine,
                movement_type='out',
                quantity=-item.quantity,  # Negative for stock out
                reference_number=self.order_number,
                notes=f'Order {self.order_number} - {item.quantity} units sold',
                created_by=self.sales_rep
            )
    
    def restore_stock(self):
        """Restore stock for all items in this order (for cancellations)"""
        from inventory.models import StockMovement
        from django.utils import timezone
        
        for item in self.items.all():
            # Restore the medicine's current stock
            item.medicine.current_stock += item.quantity
            item.medicine.save()
            
            # Create stock movement record
            StockMovement.objects.create(
                medicine=item.medicine,
                movement_type='return',
                quantity=item.quantity,  # Positive for stock return
                reference_number=f"{self.order_number}-CANCEL",
                notes=f'Order {self.order_number} cancelled - {item.quantity} units restored',
                created_by=self.sales_rep
            )
    
    def check_stock_availability(self):
        """Check if all items in the order have sufficient stock"""
        for item in self.items.all():
            if item.medicine.current_stock < item.quantity:
                return False, f"Insufficient stock for {item.medicine.name}. Available: {item.medicine.current_stock}, Required: {item.quantity}"
        return True, "Stock available"
    
    def save(self, *args, **kwargs):
        # Handle stock management based on status changes
        if self.pk:  # Only for existing orders
            old_order = Order.objects.get(pk=self.pk)
            
            # If status changed from pending to confirmed, decrease stock
            if (old_order.status == 'pending' and 
                self.status == 'confirmed' and 
                old_order.status != self.status):
                self.decrease_stock()
                self.confirmed_at = timezone.now()
            
            # If status changed to cancelled and was previously confirmed, restore stock
            elif (self.status == 'cancelled' and 
                  old_order.status in ['confirmed', 'processing', 'ready_for_pickup'] and 
                  old_order.status != self.status):
                self.restore_stock()
        
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Individual items in an order
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Prescription details for this specific item
    prescription_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['order', 'medicine']
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity} in Order {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """
    Track order status changes
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    old_payment_status = models.CharField(max_length=20, blank=True)
    new_payment_status = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"Order {self.order.order_number}: {self.old_status} -> {self.new_status}"


class Cart(models.Model):
    """
    Shopping cart for sales representatives
    """
    sales_rep = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart for {self.sales_rep.username}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_amount(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(models.Model):
    """
    Items in shopping cart
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey('inventory.Medicine', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cart', 'medicine']
    
    def __str__(self):
        return f"{self.medicine.name} x {self.quantity} in Cart"
    
    @property
    def total_price(self):
        return self.quantity * self.medicine.unit_price