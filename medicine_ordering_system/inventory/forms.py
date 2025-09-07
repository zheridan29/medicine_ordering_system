from django import forms
from .models import Medicine, Category, Manufacturer, StockMovement, ReorderAlert

class MedicineForm(forms.ModelForm):
    """Form for creating and editing medicines"""
    
    class Meta:
        model = Medicine
        fields = [
            'name', 'generic_name', 'description', 'category', 'manufacturer',
            'price', 'cost', 'stock_quantity', 'min_stock_level', 'max_stock_level',
            'unit', 'dosage_form', 'strength', 'prescription_required', 'is_active',
            'image', 'expiry_date', 'batch_number', 'barcode'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'max_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'dosage_form': forms.Select(attrs={'class': 'form-select'}),
            'strength': forms.TextInput(attrs={'class': 'form-control'}),
            'prescription_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ManufacturerForm(forms.ModelForm):
    """Form for creating and editing manufacturers"""
    
    class Meta:
        model = Manufacturer
        fields = ['name', 'contact_person', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class StockMovementForm(forms.ModelForm):
    """Form for creating stock movements"""
    
    class Meta:
        model = StockMovement
        fields = ['medicine', 'movement_type', 'quantity', 'reason', 'notes']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReorderAlertForm(forms.ModelForm):
    """Form for creating reorder alerts"""
    
    class Meta:
        model = ReorderAlert
        fields = ['medicine', 'current_stock', 'reorder_level', 'suggested_quantity', 'priority', 'notes']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'suggested_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }



