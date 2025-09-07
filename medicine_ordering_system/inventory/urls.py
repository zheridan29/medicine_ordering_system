from django.urls import path, include
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.InventoryDashboardView.as_view(), name='dashboard'),
    
    # Medicine management
    path('medicines/', views.MedicineListView.as_view(), name='medicine_list'),
    path('medicines/create/', views.MedicineCreateView.as_view(), name='medicine_create'),
    path('medicines/<int:pk>/', views.MedicineDetailView.as_view(), name='medicine_detail'),
    path('medicines/<int:pk>/edit/', views.MedicineEditView.as_view(), name='medicine_edit'),
    path('medicines/<int:pk>/delete/', views.MedicineDeleteView.as_view(), name='medicine_delete'),
    path('low-stock/', views.LowStockMedicinesView.as_view(), name='low_stock_medicines'),
    
    # Category management
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    
    # Stock management
    path('stock-movements/', views.StockMovementListView.as_view(), name='stock_movement_list'),
    path('stock-movements/create/', views.StockMovementCreateView.as_view(), name='stock_movement_create'),
    path('reorder-alerts/', views.ReorderAlertListView.as_view(), name='reorder_alert_list'),
    
    # Manufacturer management
    path('manufacturers/', views.ManufacturerListView.as_view(), name='manufacturer_list'),
    path('manufacturers/create/', views.ManufacturerCreateView.as_view(), name='manufacturer_create'),
    path('manufacturers/<int:pk>/edit/', views.ManufacturerEditView.as_view(), name='manufacturer_edit'),
    path('manufacturers/<int:pk>/delete/', views.ManufacturerDeleteView.as_view(), name='manufacturer_delete'),
    
    # API endpoints
    path('api/medicines/', views.MedicineListAPIView.as_view(), name='api_medicine_list'),
    path('api/medicines/<int:pk>/', views.MedicineDetailAPIView.as_view(), name='api_medicine_detail'),
    path('api/stock-movements/', views.StockMovementAPIView.as_view(), name='api_stock_movements'),
    path('api/reorder-alerts/', views.ReorderAlertAPIView.as_view(), name='api_reorder_alerts'),
]
