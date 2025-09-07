from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import SalesRepProfile, PharmacistAdminProfile

User = get_user_model()

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    user_type = forms.ChoiceField(
        choices=[('sales_rep', 'Sales Representative'), ('pharmacist_admin', 'Pharmacist/Admin')],
        widget=forms.RadioSelect
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['user_type'].widget.attrs.update({'class': 'form-check-input'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # Map user_type to role field
        user.role = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user

class UserEditForm(forms.ModelForm):
    """Form for editing user information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SalesRepProfileForm(forms.ModelForm):
    """Form for sales representative profile"""
    
    class Meta:
        model = SalesRepProfile
        fields = ['employee_id', 'territory', 'commission_rate', 'manager', 'is_active']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'territory': forms.TextInput(attrs={'class': 'form-control'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PharmacistAdminProfileForm(forms.ModelForm):
    """Form for pharmacist/admin profile"""
    
    class Meta:
        model = PharmacistAdminProfile
        fields = ['license_number', 'license_expiry', 'specialization', 'years_of_experience', 'department', 'is_available']
        widgets = {
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProfileEditForm(forms.ModelForm):
    """Combined form for editing user and profile information"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add profile-specific fields based on user type
        if self.instance and hasattr(self.instance, 'sales_rep_profile'):
            profile = self.instance.sales_rep_profile
            self.fields['employee_id'] = forms.CharField(
                initial=profile.employee_id,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
            self.fields['territory'] = forms.CharField(
                initial=profile.territory,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
        elif self.instance and hasattr(self.instance, 'pharmacist_admin_profile'):
            profile = self.instance.pharmacist_admin_profile
            self.fields['license_number'] = forms.CharField(
                initial=profile.license_number,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
            self.fields['specialization'] = forms.CharField(
                initial=profile.specialization,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )