from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta, date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Transaction, PaymentMethod, Refund, SalesReport


# Dashboard View
class TransactionDashboardView(LoginRequiredMixin, TemplateView):
    """Transaction dashboard"""
    template_name = 'transactions/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get transaction statistics
        today = timezone.now().date()
        this_month = today.replace(day=1)
        
        total_transactions = Transaction.objects.count()
        completed_transactions = Transaction.objects.filter(status='completed').count()
        pending_transactions = Transaction.objects.filter(status='pending').count()
        failed_transactions = Transaction.objects.filter(status='failed').count()
        
        # Revenue metrics
        total_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        monthly_revenue = Transaction.objects.filter(
            status='completed',
            created_at__date__gte=this_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Recent transactions
        recent_transactions = Transaction.objects.select_related('order', 'payment_method').order_by('-created_at')[:10]
        
        # Payment method breakdown
        payment_methods = PaymentMethod.objects.filter(is_active=True)
        
        context.update({
            'total_transactions': total_transactions,
            'completed_transactions': completed_transactions,
            'pending_transactions': pending_transactions,
            'failed_transactions': failed_transactions,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'recent_transactions': recent_transactions,
            'payment_methods': payment_methods,
        })
        
        return context


# Transaction Management Views
class TransactionListView(LoginRequiredMixin, ListView):
    """List all transactions"""
    model = Transaction
    template_name = 'transactions/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Transaction.objects.select_related('order', 'payment_method').order_by('-created_at')
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by payment method
        payment_method = self.request.GET.get('payment_method')
        if payment_method:
            queryset = queryset.filter(payment_method_id=payment_method)
        
        # Search by transaction ID or order number
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(order__order_number__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['payment_methods'] = PaymentMethod.objects.filter(is_active=True)
        return context


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Transaction detail view"""
    model = Transaction
    template_name = 'transactions/transaction_detail.html'
    context_object_name = 'transaction'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transaction = self.get_object()
        
        # Get refunds for this transaction
        refunds = Refund.objects.filter(transaction=transaction).order_by('-requested_at')
        context['refunds'] = refunds
        
        return context


class RefundCreateView(LoginRequiredMixin, CreateView):
    """Create refund for transaction"""
    model = Refund
    template_name = 'transactions/refund_form.html'
    fields = ['amount', 'reason', 'description']
    
    def get_initial(self):
        transaction = get_object_or_404(Transaction, pk=self.kwargs['pk'])
        return {
            'amount': transaction.amount,
        }
    
    def form_valid(self, form):
        transaction = get_object_or_404(Transaction, pk=self.kwargs['pk'])
        form.instance.transaction = transaction
        form.instance.order = transaction.order
        form.instance.requested_by = self.request.user
        messages.success(self.request, 'Refund request created successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('transactions:transaction_detail', kwargs={'pk': self.kwargs['pk']})


# Payment Method Management Views
class PaymentMethodListView(LoginRequiredMixin, ListView):
    """List all payment methods"""
    model = PaymentMethod
    template_name = 'transactions/payment_method_list.html'
    context_object_name = 'payment_methods'
    paginate_by = 20
    
    def get_queryset(self):
        return PaymentMethod.objects.all().order_by('name')


class PaymentMethodCreateView(LoginRequiredMixin, CreateView):
    """Create new payment method"""
    model = PaymentMethod
    template_name = 'transactions/payment_method_form.html'
    fields = ['name', 'description', 'processing_fee_percentage', 'processing_fee_fixed']
    success_url = reverse_lazy('transactions:payment_method_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method created successfully!')
        return super().form_valid(form)


class PaymentMethodEditView(LoginRequiredMixin, UpdateView):
    """Edit payment method"""
    model = PaymentMethod
    template_name = 'transactions/payment_method_form.html'
    fields = ['name', 'description', 'processing_fee_percentage', 'processing_fee_fixed', 'is_active']
    success_url = reverse_lazy('transactions:payment_method_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Payment method updated successfully!')
        return super().form_valid(form)


# Report Views
class ReportListView(LoginRequiredMixin, ListView):
    """List all reports"""
    model = SalesReport
    template_name = 'transactions/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return SalesReport.objects.all().order_by('-generated_at')


class SalesReportView(LoginRequiredMixin, TemplateView):
    """Sales report view"""
    template_name = 'transactions/sales_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if not start_date or not end_date:
            # Default to last 30 days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get sales data
        transactions = Transaction.objects.filter(
            status='completed',
            created_at__date__range=[start_date, end_date]
        )
        
        total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_transactions = transactions.count()
        
        # Payment method breakdown
        payment_breakdown = transactions.values('payment_method__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')
        
        context.update({
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': total_revenue,
            'total_transactions': total_transactions,
            'payment_breakdown': payment_breakdown,
        })
        
        return context


class FinancialReportView(LoginRequiredMixin, TemplateView):
    """Financial report view"""
    template_name = 'transactions/financial_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get financial metrics
        total_revenue = Transaction.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_refunds = Refund.objects.filter(status='processed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        net_revenue = total_revenue - total_refunds
        
        # Monthly revenue trend (last 12 months)
        monthly_data = []
        for i in range(12):
            month_start = timezone.now().date().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_revenue = Transaction.objects.filter(
                status='completed',
                created_at__date__range=[month_start, month_end]
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': month_revenue
            })
        
        context.update({
            'total_revenue': total_revenue,
            'total_refunds': total_refunds,
            'net_revenue': net_revenue,
            'monthly_data': monthly_data,
        })
        
        return context


# API Views
class TransactionListAPIView(APIView):
    """API view for transaction list"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        transactions = Transaction.objects.select_related('order', 'payment_method').order_by('-created_at')
        
        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(transactions, per_page)
        page_obj = paginator.get_page(page)
        
        transactions_data = []
        for transaction in page_obj:
            transactions_data.append({
                'id': transaction.id,
                'transaction_id': transaction.transaction_id,
                'order_number': transaction.order.order_number,
                'payment_method': transaction.payment_method.name,
                'amount': float(transaction.amount),
                'status': transaction.status,
                'created_at': transaction.created_at,
            })
        
        return Response({
            'transactions': transactions_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })


class TransactionDetailAPIView(APIView):
    """API view for transaction detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            transaction = Transaction.objects.get(pk=pk)
            return Response({
                'id': transaction.id,
                'transaction_id': transaction.transaction_id,
                'order': {
                    'id': transaction.order.id,
                    'order_number': transaction.order.order_number,
                },
                'payment_method': {
                    'id': transaction.payment_method.id,
                    'name': transaction.payment_method.name,
                },
                'transaction_type': transaction.transaction_type,
                'status': transaction.status,
                'amount': float(transaction.amount),
                'processing_fee': float(transaction.processing_fee),
                'net_amount': float(transaction.net_amount),
                'gateway_transaction_id': transaction.gateway_transaction_id,
                'created_at': transaction.created_at,
                'processed_at': transaction.processed_at,
                'completed_at': transaction.completed_at,
                'notes': transaction.notes,
                'failure_reason': transaction.failure_reason,
            })
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)


class PaymentMethodAPIView(APIView):
    """API view for payment methods"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        payment_methods = PaymentMethod.objects.filter(is_active=True)
        
        methods_data = []
        for method in payment_methods:
            methods_data.append({
                'id': method.id,
                'name': method.name,
                'description': method.description,
                'processing_fee_percentage': float(method.processing_fee_percentage),
                'processing_fee_fixed': float(method.processing_fee_fixed),
            })
        
        return Response({'payment_methods': methods_data})


class SalesReportAPIView(APIView):
    """API view for sales report"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        transactions = Transaction.objects.filter(
            status='completed',
            created_at__date__range=[start_date, end_date]
        )
        
        total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_transactions = transactions.count()
        
        # Payment method breakdown
        payment_breakdown = transactions.values('payment_method__name').annotate(
            count=Count('id'),
            total=Sum('amount')
        ).order_by('-total')
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': float(total_revenue),
            'total_transactions': total_transactions,
            'payment_breakdown': list(payment_breakdown),
        })
