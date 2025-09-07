from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Supports multiple user roles: Customer, Pharmacist, Admin
    """
    ROLE_CHOICES = [
        ('sales_rep', 'Sales Representative'),
        ('pharmacist_admin', 'Pharmacist/Admin'),
        ('admin', 'Admin'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales_rep')
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='USA')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_sales_rep(self):
        return self.role == 'sales_rep'
    
    @property
    def is_pharmacist_admin(self):
        return self.role == 'pharmacist_admin'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def can_manage_inventory(self):
        """Can manage inventory (Pharmacist/Admin and Admin)"""
        return self.role in ['pharmacist_admin', 'admin']
    
    @property
    def can_view_analytics(self):
        """Can view analytics (Pharmacist/Admin and Admin)"""
        return self.role in ['pharmacist_admin', 'admin']
    
    @property
    def can_manage_orders(self):
        """Can manage orders (All roles)"""
        return True


class SalesRepProfile(models.Model):
    """
    Extended profile for sales representatives
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sales_rep_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    territory = models.CharField(max_length=100, blank=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_sales_reps')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Sales Rep Profile for {self.user.username}"


class PharmacistAdminProfile(models.Model):
    """
    Extended profile for pharmacist/admins
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pharmacist_admin_profile')
    license_number = models.CharField(max_length=50, unique=True)
    license_expiry = models.DateField()
    specialization = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    department = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Pharmacist/Admin Profile for {self.user.username}"


class UserSession(models.Model):
    """
    Track user sessions for analytics and security
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Session for {self.user.username} at {self.login_time}"