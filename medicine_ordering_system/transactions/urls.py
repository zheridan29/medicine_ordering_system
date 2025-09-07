from django.urls import path, include
from . import views

app_name = 'transactions'

urlpatterns = [
    # Dashboard
    path('', views.TransactionDashboardView.as_view(), name='dashboard'),
    
    # Transaction management
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<int:pk>/refund/', views.RefundCreateView.as_view(), name='refund_create'),
    
    # Payment methods
    path('payment-methods/', views.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('payment-methods/create/', views.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('payment-methods/<int:pk>/edit/', views.PaymentMethodEditView.as_view(), name='payment_method_edit'),
    
    # Reports
    path('reports/', views.ReportListView.as_view(), name='report_list'),
    path('reports/sales/', views.SalesReportView.as_view(), name='sales_report'),
    path('reports/financial/', views.FinancialReportView.as_view(), name='financial_report'),
    
    # API endpoints
    path('api/transactions/', views.TransactionListAPIView.as_view(), name='api_transaction_list'),
    path('api/transactions/<int:pk>/', views.TransactionDetailAPIView.as_view(), name='api_transaction_detail'),
    path('api/payment-methods/', views.PaymentMethodAPIView.as_view(), name='api_payment_methods'),
    path('api/reports/sales/', views.SalesReportAPIView.as_view(), name='api_sales_report'),
]
