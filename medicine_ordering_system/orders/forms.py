from django import forms
from django.contrib.auth import get_user_model
from .models import Order, OrderItem, Cart, CartItem
from inventory.models import Medicine
from common.models import Address

User = get_user_model()

class OrderForm(forms.ModelForm):
    """Form for creating and editing orders"""
    
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_phone', 'customer_address', 'delivery_method', 'delivery_address', 'delivery_instructions', 'payment_status', 'customer_notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OrderWithItemsForm(forms.ModelForm):
    """Form for creating orders with medicine selection"""
    
    # Medicine selection fields
    medicine_1 = forms.ModelChoiceField(
        queryset=Medicine.objects.none(),
        required=False,
        empty_label="Select Medicine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_1 = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Quantity'})
    )
    
    medicine_2 = forms.ModelChoiceField(
        queryset=Medicine.objects.none(),
        required=False,
        empty_label="Select Medicine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_2 = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Quantity'})
    )
    
    medicine_3 = forms.ModelChoiceField(
        queryset=Medicine.objects.none(),
        required=False,
        empty_label="Select Medicine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_3 = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Quantity'})
    )
    
    medicine_4 = forms.ModelChoiceField(
        queryset=Medicine.objects.none(),
        required=False,
        empty_label="Select Medicine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_4 = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Quantity'})
    )
    
    medicine_5 = forms.ModelChoiceField(
        queryset=Medicine.objects.none(),
        required=False,
        empty_label="Select Medicine",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity_5 = forms.IntegerField(
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Quantity'})
    )
    
    class Meta:
        model = Order
        fields = ['delivery_method', 'delivery_address', 'delivery_instructions', 'payment_status', 'customer_notes']
        widgets = {
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for medicine fields
        medicine_queryset = Medicine.objects.filter(is_active=True, is_available=True).order_by('name')
        self.fields['medicine_1'].queryset = medicine_queryset
        self.fields['medicine_2'].queryset = medicine_queryset
        self.fields['medicine_3'].queryset = medicine_queryset
        self.fields['medicine_4'].queryset = medicine_queryset
        self.fields['medicine_5'].queryset = medicine_queryset
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Check if at least one medicine is selected
        medicines = []
        for i in range(1, 6):
            medicine = cleaned_data.get(f'medicine_{i}')
            quantity = cleaned_data.get(f'quantity_{i}')
            
            if medicine and quantity:
                medicines.append((medicine, quantity))
            elif medicine and not quantity:
                raise forms.ValidationError(f"Please enter quantity for {medicine.name}")
            elif not medicine and quantity:
                raise forms.ValidationError("Please select a medicine for the quantity entered")
        
        if not medicines:
            raise forms.ValidationError("Please select at least one medicine for the order")
        
        return cleaned_data

class OrderItemForm(forms.ModelForm):
    """Form for adding items to orders"""
    
    class Meta:
        model = OrderItem
        fields = ['medicine', 'quantity']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class CartAddForm(forms.ModelForm):
    """Form for adding items to cart"""
    
    class Meta:
        model = CartItem
        fields = ['medicine', 'quantity']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class OrderStatusUpdateForm(forms.ModelForm):
    """Form for updating order status"""
    
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'internal_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = Order.STATUS_CHOICES
        self.fields['payment_status'].choices = Order.PAYMENT_STATUS_CHOICES

class PrescriptionUploadForm(forms.ModelForm):
    """Form for uploading prescriptions"""
    
    class Meta:
        model = Order
        fields = ['prescription_image', 'customer_notes']
        widgets = {
            'prescription_image': forms.FileInput(attrs={'class': 'form-control', 'accept': '.jpg,.jpeg,.png,.pdf'}),
            'customer_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes about the prescription'}),
        }

class PrescriptionVerifyForm(forms.ModelForm):
    """Form for verifying prescriptions"""
    
    class Meta:
        model = Order
        fields = ['prescription_verified', 'internal_notes', 'verified_by']
        widgets = {
            'prescription_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'verified_by': forms.Select(attrs={'class': 'form-select'}),
        }

class OrderCancelForm(forms.ModelForm):
    """Form for cancelling orders"""
    
    class Meta:
        model = Order
        fields = ['internal_notes']
        widgets = {
            'internal_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Please provide a reason for cancelling this order'}),
        }



