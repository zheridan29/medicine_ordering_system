from django import forms
from .models import Transaction, PaymentMethod, Refund, SalesReport

class TransactionForm(forms.ModelForm):
    """Form for creating and editing transactions"""
    
    class Meta:
        model = Transaction
        fields = [
            'order', 'payment_method', 'amount', 'transaction_type', 
            'status', 'gateway_transaction_id', 'gateway_response', 'notes'
        ]
        widgets = {
            'order': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'gateway_transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'gateway_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PaymentMethodForm(forms.ModelForm):
    """Form for creating and editing payment methods"""
    
    class Meta:
        model = PaymentMethod
        fields = ['name', 'payment_type', 'is_active', 'processing_fee_percentage', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'processing_fee_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class RefundForm(forms.ModelForm):
    """Form for creating refunds"""
    
    class Meta:
        model = Refund
        fields = [
            'transaction', 'refund_amount', 'refund_reason', 'refund_type',
            'status', 'notes', 'processed_by'
        ]
        widgets = {
            'transaction': forms.Select(attrs={'class': 'form-select'}),
            'refund_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'refund_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'refund_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'processed_by': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SalesReportForm(forms.ModelForm):
    """Form for generating sales reports"""
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = SalesReport
        fields = ['report_type', 'start_date', 'end_date', 'include_details']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'include_details': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



