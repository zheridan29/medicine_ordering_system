from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Medicine, Category, Manufacturer, StockMovement, ReorderAlert, MedicineImage


# Dashboard View
class InventoryDashboardView(LoginRequiredMixin, TemplateView):
    """Inventory dashboard for pharmacists"""
    template_name = 'inventory/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get basic statistics
        total_medicines = Medicine.objects.filter(is_active=True).count()
        low_stock_medicines = Medicine.objects.filter(
            is_active=True,
            current_stock__lte=F('reorder_point')
        ).count()
        out_of_stock_medicines = Medicine.objects.filter(
            is_active=True,
            current_stock=0
        ).count()
        total_categories = Category.objects.filter(is_active=True).count()
        total_manufacturers = Manufacturer.objects.filter(is_active=True).count()
        
        # Recent stock movements
        recent_movements = StockMovement.objects.select_related('medicine').order_by('-created_at')[:10]
        
        # Reorder alerts
        pending_alerts = ReorderAlert.objects.filter(is_processed=False).order_by('-priority', '-created_at')[:5]
        
        context.update({
            'total_medicines': total_medicines,
            'low_stock_medicines': low_stock_medicines,
            'out_of_stock_medicines': out_of_stock_medicines,
            'total_categories': total_categories,
            'total_manufacturers': total_manufacturers,
            'recent_movements': recent_movements,
            'pending_alerts': pending_alerts,
        })
        
        return context


# Medicine Management Views
class MedicineListView(LoginRequiredMixin, ListView):
    """List all medicines"""
    model = Medicine
    template_name = 'inventory/medicine_list.html'
    context_object_name = 'medicines'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Medicine.objects.select_related('category', 'manufacturer').filter(is_active=True)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(category__name__icontains=search) |
                Q(manufacturer__name__icontains=search)
            )
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by stock status
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low':
            queryset = queryset.filter(current_stock__lte=F('reorder_point'))
        elif stock_status == 'out':
            queryset = queryset.filter(current_stock=0)
        
        return queryset.order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        return context


class MedicineDetailView(LoginRequiredMixin, DetailView):
    """Medicine detail view"""
    model = Medicine
    template_name = 'inventory/medicine_detail.html'
    context_object_name = 'medicine'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        medicine = self.get_object()
        
        # Get recent stock movements for this medicine
        recent_movements = StockMovement.objects.filter(medicine=medicine).order_by('-created_at')[:10]
        context['recent_movements'] = recent_movements
        
        return context


class MedicineCreateView(LoginRequiredMixin, CreateView):
    """Create new medicine - only for pharmacist/admin and admin"""
    model = Medicine
    template_name = 'inventory/medicine_form.html'
    fields = [
        'name', 'generic_name', 'description', 'category', 'manufacturer',
        'dosage_form', 'strength', 'prescription_type', 'unit_price', 'cost_price',
        'current_stock', 'minimum_stock_level', 'maximum_stock_level', 'reorder_point',
        'weight', 'dimensions', 'storage_conditions', 'ndc_number',
        'fda_approval_date', 'expiry_date', 'is_available', 'requires_prescription'
    ]
    success_url = reverse_lazy('inventory:medicine_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can create medicines.')
            return redirect('inventory:medicine_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Medicine created successfully!')
        return super().form_valid(form)


class MedicineEditView(LoginRequiredMixin, UpdateView):
    """Edit medicine - only for pharmacist/admin and admin"""
    model = Medicine
    template_name = 'inventory/medicine_form.html'
    fields = [
        'name', 'generic_name', 'description', 'category', 'manufacturer',
        'dosage_form', 'strength', 'prescription_type', 'unit_price', 'cost_price',
        'current_stock', 'minimum_stock_level', 'maximum_stock_level', 'reorder_point',
        'weight', 'dimensions', 'storage_conditions', 'ndc_number',
        'fda_approval_date', 'expiry_date', 'is_available', 'requires_prescription'
    ]
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can edit medicines.')
            return redirect('inventory:medicine_list')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('inventory:medicine_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Medicine updated successfully!')
        return super().form_valid(form)


class MedicineDeleteView(LoginRequiredMixin, DeleteView):
    """Delete medicine (soft delete) - only for pharmacist/admin and admin"""
    model = Medicine
    template_name = 'inventory/medicine_confirm_delete.html'
    success_url = reverse_lazy('inventory:medicine_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can delete medicines.')
            return redirect('inventory:medicine_list')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        medicine = self.get_object()
        medicine.is_active = False
        medicine.save()
        messages.success(request, 'Medicine deleted successfully!')
        return redirect(self.success_url)


# Category Management Views
class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories"""
    model = Category
    template_name = 'inventory/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create new category - only for pharmacist/admin and admin"""
    model = Category
    template_name = 'inventory/category_form.html'
    fields = ['name', 'description', 'parent_category']
    success_url = reverse_lazy('inventory:category_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can create categories.')
            return redirect('inventory:category_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)


class CategoryEditView(LoginRequiredMixin, UpdateView):
    """Edit category - only for pharmacist/admin and admin"""
    model = Category
    template_name = 'inventory/category_form.html'
    fields = ['name', 'description', 'parent_category']
    success_url = reverse_lazy('inventory:category_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can edit categories.')
            return redirect('inventory:category_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)


# Stock Management Views
class StockMovementListView(LoginRequiredMixin, ListView):
    """List all stock movements"""
    model = StockMovement
    template_name = 'inventory/stock_movement_list.html'
    context_object_name = 'movements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StockMovement.objects.select_related('medicine', 'created_by').order_by('-created_at')
        
        # Filter by medicine
        medicine_id = self.request.GET.get('medicine')
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)
        
        # Filter by movement type
        movement_type = self.request.GET.get('movement_type')
        if movement_type:
            queryset = queryset.filter(movement_type=movement_type)
        
        return queryset


class StockMovementCreateView(LoginRequiredMixin, CreateView):
    """Create new stock movement - only for pharmacist/admin and admin"""
    model = StockMovement
    template_name = 'inventory/stock_movement_form.html'
    fields = ['medicine', 'movement_type', 'quantity', 'reference_number', 'notes']
    success_url = reverse_lazy('inventory:stock_movement_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can create stock movements.')
            return redirect('inventory:stock_movement_list')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Stock movement recorded successfully!')
        return super().form_valid(form)


class LowStockMedicinesView(LoginRequiredMixin, ListView):
    """List all medicines with low stock"""
    model = Medicine
    template_name = 'inventory/low_stock_medicines.html'
    context_object_name = 'medicines'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Medicine.objects.select_related('category', 'manufacturer').filter(
            is_active=True,
            current_stock__lte=F('reorder_point')
        ).order_by('current_stock', 'name')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(category__name__icontains=search) |
                Q(manufacturer__name__icontains=search)
            )
        
        # Filter by stock level
        stock_level = self.request.GET.get('stock_level')
        if stock_level == 'critical':
            queryset = queryset.filter(current_stock=0)
        elif stock_level == 'low':
            queryset = queryset.filter(current_stock__gt=0, current_stock__lte=F('reorder_point'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        total_low_stock = Medicine.objects.filter(
            is_active=True,
            current_stock__lte=F('reorder_point')
        ).count()
        
        critical_stock = Medicine.objects.filter(
            is_active=True,
            current_stock=0
        ).count()
        
        low_stock = total_low_stock - critical_stock
        
        context.update({
            'total_low_stock': total_low_stock,
            'critical_stock': critical_stock,
            'low_stock': low_stock,
            'categories': Category.objects.filter(is_active=True),
        })
        
        return context


class ReorderAlertListView(LoginRequiredMixin, ListView):
    """List all reorder alerts"""
    model = ReorderAlert
    template_name = 'inventory/reorder_alert_list.html'
    context_object_name = 'alerts'
    paginate_by = 20
    
    def get_queryset(self):
        return ReorderAlert.objects.filter(is_processed=False).order_by('-priority', '-created_at')


# Manufacturer Management Views
class ManufacturerListView(LoginRequiredMixin, ListView):
    """List all manufacturers"""
    model = Manufacturer
    template_name = 'inventory/manufacturer_list.html'
    context_object_name = 'manufacturers'
    paginate_by = 20
    
    def get_queryset(self):
        return Manufacturer.objects.filter(is_active=True).order_by('name')


class ManufacturerCreateView(LoginRequiredMixin, CreateView):
    """Create new manufacturer"""
    model = Manufacturer
    template_name = 'inventory/manufacturer_form.html'
    fields = ['name', 'country', 'contact_email', 'contact_phone', 'website']
    success_url = reverse_lazy('inventory:manufacturer_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can manage manufacturers.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Manufacturer created successfully!')
        return super().form_valid(form)


class ManufacturerEditView(LoginRequiredMixin, UpdateView):
    """Edit manufacturer"""
    model = Manufacturer
    template_name = 'inventory/manufacturer_form.html'
    fields = ['name', 'country', 'contact_email', 'contact_phone', 'website']
    success_url = reverse_lazy('inventory:manufacturer_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can manage manufacturers.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Manufacturer updated successfully!')
        return super().form_valid(form)


class ManufacturerDeleteView(LoginRequiredMixin, DeleteView):
    """Delete manufacturer (soft delete)"""
    model = Manufacturer
    template_name = 'inventory/manufacturer_confirm_delete.html'
    success_url = reverse_lazy('inventory:manufacturer_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_admin or request.user.is_pharmacist_admin):
            messages.error(request, 'Only administrators and pharmacists can manage manufacturers.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        manufacturer = self.get_object()
        manufacturer.is_active = False
        manufacturer.save()
        messages.success(request, 'Manufacturer deleted successfully!')
        return redirect(self.success_url)


# API Views
class MedicineListAPIView(APIView):
    """API view for medicine list"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        medicines = Medicine.objects.filter(is_active=True).select_related('category', 'manufacturer')
        
        # Search functionality
        search = request.GET.get('search')
        if search:
            medicines = medicines.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search)
            )
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(medicines, per_page)
        page_obj = paginator.get_page(page)
        
        medicines_data = []
        for medicine in page_obj:
            medicines_data.append({
                'id': medicine.id,
                'name': medicine.name,
                'generic_name': medicine.generic_name,
                'strength': medicine.strength,
                'dosage_form': medicine.dosage_form,
                'unit_price': float(medicine.unit_price),
                'current_stock': medicine.current_stock,
                'stock_status': medicine.stock_status,
                'category': medicine.category.name,
                'manufacturer': medicine.manufacturer.name,
            })
        
        return Response({
            'medicines': medicines_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })


class MedicineDetailAPIView(APIView):
    """API view for medicine detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            medicine = Medicine.objects.get(pk=pk, is_active=True)
            return Response({
                'id': medicine.id,
                'name': medicine.name,
                'generic_name': medicine.generic_name,
                'description': medicine.description,
                'strength': medicine.strength,
                'dosage_form': medicine.dosage_form,
                'prescription_type': medicine.prescription_type,
                'unit_price': float(medicine.unit_price),
                'cost_price': float(medicine.cost_price),
                'current_stock': medicine.current_stock,
                'minimum_stock_level': medicine.minimum_stock_level,
                'maximum_stock_level': medicine.maximum_stock_level,
                'reorder_point': medicine.reorder_point,
                'stock_status': medicine.stock_status,
                'is_available': medicine.is_available,
                'requires_prescription': medicine.requires_prescription,
                'category': {
                    'id': medicine.category.id,
                    'name': medicine.category.name,
                },
                'manufacturer': {
                    'id': medicine.manufacturer.id,
                    'name': medicine.manufacturer.name,
                },
            })
        except Medicine.DoesNotExist:
            return Response({'error': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)


class StockMovementAPIView(APIView):
    """API view for stock movements"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        movements = StockMovement.objects.select_related('medicine', 'created_by').order_by('-created_at')
        
        # Filter by medicine
        medicine_id = request.GET.get('medicine')
        if medicine_id:
            movements = movements.filter(medicine_id=medicine_id)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(movements, per_page)
        page_obj = paginator.get_page(page)
        
        movements_data = []
        for movement in page_obj:
            movements_data.append({
                'id': movement.id,
                'medicine': {
                    'id': movement.medicine.id,
                    'name': movement.medicine.name,
                },
                'movement_type': movement.movement_type,
                'quantity': movement.quantity,
                'reference_number': movement.reference_number,
                'notes': movement.notes,
                'created_by': movement.created_by.username,
                'created_at': movement.created_at,
            })
        
        return Response({
            'movements': movements_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })


class ReorderAlertAPIView(APIView):
    """API view for reorder alerts"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        alerts = ReorderAlert.objects.filter(is_processed=False).order_by('-priority', '-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(alerts, per_page)
        page_obj = paginator.get_page(page)
        
        alerts_data = []
        for alert in page_obj:
            alerts_data.append({
                'id': alert.id,
                'medicine': {
                    'id': alert.medicine.id,
                    'name': alert.medicine.name,
                },
                'current_stock': alert.current_stock,
                'reorder_point': alert.reorder_point,
                'suggested_quantity': alert.suggested_quantity,
                'priority': alert.priority,
                'created_at': alert.created_at,
            })
        
        return Response({
            'alerts': alerts_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })
