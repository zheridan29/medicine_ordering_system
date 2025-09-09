from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import Order, OrderItem, OrderStatusHistory, Cart, CartItem
from .forms import OrderForm, OrderWithItemsForm, OrderStatusUpdateForm, PrescriptionUploadForm, PrescriptionVerifyForm, OrderCancelForm, CartAddForm


# Dashboard View
class OrderDashboardView(LoginRequiredMixin, TemplateView):
    """Order dashboard for sales representatives"""
    template_name = 'orders/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's orders
        recent_orders = Order.objects.filter(sales_rep=user).order_by('-created_at')[:5]
        
        # Get order statistics
        total_orders = Order.objects.filter(sales_rep=user).count()
        pending_orders = Order.objects.filter(sales_rep=user, status='pending').count()
        completed_orders = Order.objects.filter(sales_rep=user, status='delivered').count()
        
        # Get cart information
        cart, created = Cart.objects.get_or_create(sales_rep=user)
        cart_items = cart.items.all()
        
        context.update({
            'recent_orders': recent_orders,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'cart_items': cart_items,
            'cart_total': cart.total_amount,
        })
        
        return context


# Order Management Views
class OrderListView(LoginRequiredMixin, ListView):
    """List all orders for the current user or all orders for pharmacist/admin"""
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        if user.is_pharmacist_admin or user.is_admin:
            # Pharmacist/Admin and Admin can see all orders from sales reps
            return Order.objects.all().order_by('-created_at')
        else:
            # Sales reps can only see their own orders
            return Order.objects.filter(sales_rep=user).order_by('-created_at')


class OrderCreateView(LoginRequiredMixin, CreateView):
    """Create new order with medicine selection"""
    model = Order
    template_name = 'orders/order_form.html'
    form_class = OrderWithItemsForm
    success_url = reverse_lazy('orders:order_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Order creation is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_initial(self):
        """Pre-populate form with cart items and sales rep details"""
        initial = super().get_initial()
        
        # Pre-populate delivery address with sales rep address
        user = self.request.user
        initial['delivery_address'] = getattr(user, 'address', '') or ''
        
        # Check if user has cart items and pre-populate the form
        try:
            cart = Cart.objects.get(sales_rep=self.request.user)
            cart_items = cart.items.select_related('medicine').all()
            
            # Pre-populate medicine fields with cart items
            for i, item in enumerate(cart_items[:5], 1):  # Limit to 5 items
                initial[f'medicine_{i}'] = item.medicine
                initial[f'quantity_{i}'] = item.quantity
                
        except Cart.DoesNotExist:
            pass
            
        return initial
    
    def form_valid(self, form):
        # Set the sales rep
        form.instance.sales_rep = self.request.user
        
        # Set customer details from sales rep information (since sales rep is the one ordering)
        user = self.request.user
        form.instance.customer_name = user.get_full_name() or user.username
        form.instance.customer_phone = getattr(user, 'phone', '') or ''
        form.instance.customer_address = getattr(user, 'address', '') or ''
        
        # Set delivery address to sales rep address if not provided
        if not form.instance.delivery_address:
            form.instance.delivery_address = getattr(user, 'address', '') or ''
        
        # Calculate totals before saving
        subtotal = Decimal('0.00')
        medicines_data = []
        
        # Collect medicine data and calculate subtotal
        for i in range(1, 6):
            medicine = form.cleaned_data.get(f'medicine_{i}')
            quantity = form.cleaned_data.get(f'quantity_{i}')
            
            if medicine and quantity:
                # Check stock availability before creating order
                if medicine.current_stock < quantity:
                    messages.error(self.request, f'Insufficient stock for {medicine.name}. Available: {medicine.current_stock}, Requested: {quantity}')
                    return self.form_invalid(form)
                
                item_total = medicine.unit_price * quantity
                subtotal += item_total
                medicines_data.append({
                    'medicine': medicine,
                    'quantity': quantity,
                    'unit_price': medicine.unit_price,
                    'total_price': item_total
                })
        
        # Set order totals
        form.instance.subtotal = subtotal
        form.instance.tax_amount = subtotal * Decimal('0.08')  # 8% tax
        form.instance.shipping_cost = Decimal('10.00') if form.cleaned_data.get('delivery_method') == 'delivery' else Decimal('0.00')
        form.instance.discount_amount = Decimal('0.00')
        form.instance.total_amount = subtotal + form.instance.tax_amount + form.instance.shipping_cost - form.instance.discount_amount
        
        # Save the order first
        response = super().form_valid(form)
        
        # Create order items from the selected medicines
        for medicine_data in medicines_data:
            OrderItem.objects.create(
                order=self.object,
                medicine=medicine_data['medicine'],
                quantity=medicine_data['quantity'],
                unit_price=medicine_data['unit_price'],
                total_price=medicine_data['total_price']
            )
        
        # Clear the cart after successful order creation
        try:
            cart = Cart.objects.get(sales_rep=self.request.user)
            cart.items.all().delete()
            messages.success(self.request, 'Sales order created successfully and cart cleared!')
        except Cart.DoesNotExist:
            messages.success(self.request, 'Sales order created successfully!')
        
        return response


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail view"""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        user = self.request.user
        if user.is_pharmacist_admin or user.is_admin:
            # Pharmacist/Admin and Admin can view any order
            return Order.objects.all()
        else:
            # Sales reps can only view their own orders
            return Order.objects.filter(sales_rep=user)


class OrderEditView(LoginRequiredMixin, UpdateView):
    """Edit order"""
    model = Order
    template_name = 'orders/order_form.html'
    form_class = OrderForm
    
    def get_queryset(self):
        user = self.request.user
        if user.is_pharmacist_admin or user.is_admin:
            # Pharmacist/Admin and Admin can edit any order
            return Order.objects.all()
        else:
            # Sales reps can only edit their own orders
            return Order.objects.filter(sales_rep=user)
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Order updated successfully!')
        return super().form_valid(form)


class OrderCancelView(LoginRequiredMixin, UpdateView):
    """Cancel order"""
    model = Order
    template_name = 'orders/order_confirm_cancel.html'
    fields = []
    
    def get_queryset(self):
        user = self.request.user
        if user.is_pharmacist_admin or user.is_admin:
            # Pharmacist/Admin and Admin can cancel any order
            return Order.objects.filter(status__in=['pending', 'confirmed'])
        else:
            # Sales reps can only cancel their own orders
            return Order.objects.filter(sales_rep=user, status__in=['pending', 'confirmed'])
    
    def form_valid(self, form):
        self.object.status = 'cancelled'
        self.object.save()
        messages.success(self.request, 'Order cancelled successfully!')
        return redirect('orders:order_detail', pk=self.object.pk)


# Cart Management Views
class CartView(LoginRequiredMixin, TemplateView):
    """Shopping cart view - only for sales reps"""
    template_name = 'orders/cart.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Cart access is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(sales_rep=self.request.user)
        cart_items = cart.items.select_related('medicine').all()
        
        # Calculate cart totals
        cart_subtotal = sum(item.total_price for item in cart_items)
        cart_tax = cart_subtotal * Decimal('0.08')  # 8% tax
        cart_shipping = Decimal('10.00')  # Fixed shipping cost
        cart_total = cart_subtotal + cart_tax + cart_shipping
        
        context.update({
            'cart_items': cart_items,
            'cart_subtotal': cart_subtotal,
            'cart_tax': cart_tax,
            'cart_shipping': cart_shipping,
            'cart_total': cart_total,
        })
        return context


class CartAddView(LoginRequiredMixin, CreateView):
    """Add item to cart - only for sales reps"""
    model = CartItem
    fields = ['medicine', 'quantity']
    success_url = reverse_lazy('orders:cart')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Cart access is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        cart, created = Cart.objects.get_or_create(sales_rep=self.request.user)
        form.instance.cart = cart
        
        # Check if item already exists in cart
        existing_item = CartItem.objects.filter(cart=cart, medicine=form.instance.medicine).first()
        if existing_item:
            existing_item.quantity += form.instance.quantity
            existing_item.save()
            messages.success(self.request, 'Item quantity updated in cart!')
        else:
            form.save()
            messages.success(self.request, 'Item added to cart!')
        
        return redirect(self.success_url)


class CartRemoveView(LoginRequiredMixin, DeleteView):
    """Remove item from cart - only for sales reps"""
    model = CartItem
    success_url = reverse_lazy('orders:cart')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Cart access is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(sales_rep=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Item removed from cart!')
        return super().delete(request, *args, **kwargs)


class CartUpdateView(LoginRequiredMixin, UpdateView):
    """Update cart item quantity - only for sales reps"""
    model = CartItem
    fields = ['quantity']
    success_url = reverse_lazy('orders:cart')
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Cart access is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(sales_rep=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def form_valid(self, form):
        messages.success(self.request, 'Cart updated!')
        return super().form_valid(form)


class CartClearView(LoginRequiredMixin, TemplateView):
    """Clear entire cart - only for sales reps"""
    template_name = 'orders/cart_confirm_clear.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Cart access is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart, created = Cart.objects.get_or_create(sales_rep=self.request.user)
        context['cart_items'] = cart.items.select_related('medicine').all()
        return context
    
    def post(self, request, *args, **kwargs):
        cart, created = Cart.objects.get_or_create(sales_rep=request.user)
        cart.items.all().delete()
        messages.success(request, 'Cart cleared!')
        return redirect('orders:cart')


# Order Status Management

class PrescriptionUploadView(LoginRequiredMixin, UpdateView):
    """Upload prescription for order - only for sales reps"""
    model = Order
    fields = ['prescription_image', 'prescription_notes']
    template_name = 'orders/prescription_upload.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_sales_rep:
            messages.error(request, 'Prescription upload is only available for sales representatives.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Sales reps can only upload prescriptions for their own orders
        return Order.objects.filter(sales_rep=self.request.user)
    
    def get_success_url(self):
        return reverse('orders:order_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.prescription_required = True
        messages.success(self.request, 'Prescription uploaded successfully!')
        return super().form_valid(form)


class PrescriptionVerifyView(LoginRequiredMixin, UpdateView):
    """Verify prescription (pharmacist only)"""
    model = Order
    fields = ['prescription_verified', 'internal_notes']
    template_name = 'orders/prescription_verify.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not (request.user.is_pharmacist_admin or request.user.is_admin):
            messages.error(request, 'Prescription verification is only available for pharmacists and administrators.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Pharmacist/Admin and Admin can verify prescriptions for any order
        return Order.objects.all()
    
    def form_valid(self, form):
        if form.cleaned_data['prescription_verified']:
            form.instance.verified_by = self.request.user
            form.instance.verified_at = timezone.now()
        
        messages.success(self.request, 'Prescription verification updated!')
        return super().form_valid(form)


# API Views
class OrderListAPIView(APIView):
    """API view for order list"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if user.is_pharmacist_admin or user.is_admin:
            # Pharmacist/Admin and Admin can see all orders
            orders = Order.objects.all().order_by('-created_at')
        else:
            # Sales reps can only see their own orders
            orders = Order.objects.filter(sales_rep=user).order_by('-created_at')
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(orders, per_page)
        page_obj = paginator.get_page(page)
        
        orders_data = []
        for order in page_obj:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at,
                'delivery_method': order.delivery_method,
            })
        
        return Response({
            'orders': orders_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })


class OrderDetailAPIView(APIView):
    """API view for order detail"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            user = request.user
            if user.is_pharmacist_admin or user.is_admin:
                # Pharmacist/Admin and Admin can view any order
                order = Order.objects.get(pk=pk)
            else:
                # Sales reps can only view their own orders
                order = Order.objects.get(pk=pk, sales_rep=user)
            items_data = []
            for item in order.items.all():
                items_data.append({
                    'medicine': {
                        'id': item.medicine.id,
                        'name': item.medicine.name,
                        'strength': item.medicine.strength,
                    },
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                })
            
            return Response({
                'id': order.id,
                'order_number': order.order_number,
                'status': order.status,
                'payment_status': order.payment_status,
                'subtotal': float(order.subtotal),
                'tax_amount': float(order.tax_amount),
                'shipping_cost': float(order.shipping_cost),
                'discount_amount': float(order.discount_amount),
                'total_amount': float(order.total_amount),
                'delivery_method': order.delivery_method,
                'delivery_address': order.delivery_address,
                'prescription_required': order.prescription_required,
                'prescription_verified': order.prescription_verified,
                'created_at': order.created_at,
                'items': items_data,
            })
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


class CartAPIView(APIView):
    """API view for cart - only for sales reps"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_sales_rep:
            return Response({'error': 'Cart access is only available for sales representatives'}, status=status.HTTP_403_FORBIDDEN)
        
        cart, created = Cart.objects.get_or_create(sales_rep=request.user)
        items_data = []
        for item in cart.items.select_related('medicine').all():
            items_data.append({
                'id': item.id,
                'medicine': {
                    'id': item.medicine.id,
                    'name': item.medicine.name,
                    'strength': item.medicine.strength,
                    'unit_price': float(item.medicine.unit_price),
                },
                'quantity': item.quantity,
                'total_price': float(item.total_price),
            })
        
        return Response({
            'items': items_data,
            'total_amount': float(cart.total_amount),
            'total_items': cart.total_items,
        })


class CartAddAPIView(APIView):
    """API view for adding item to cart - only for sales reps"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_sales_rep:
            return Response({'error': 'Cart access is only available for sales representatives'}, status=status.HTTP_403_FORBIDDEN)
        
        medicine_id = request.data.get('medicine_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            from inventory.models import Medicine
            medicine = Medicine.objects.get(id=medicine_id, is_active=True, is_available=True)
            
            cart, created = Cart.objects.get_or_create(sales_rep=request.user)
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                medicine=medicine,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response({'message': 'Item added to cart successfully'})
        except Medicine.DoesNotExist:
            return Response({'error': 'Medicine not found'}, status=status.HTTP_404_NOT_FOUND)


class CartRemoveAPIView(APIView):
    """API view for removing item from cart - only for sales reps"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, item_id):
        if not request.user.is_sales_rep:
            return Response({'error': 'Cart access is only available for sales representatives'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            cart, created = Cart.objects.get_or_create(sales_rep=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response({'message': 'Item removed from cart successfully'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)


class CartUpdateAPIView(APIView):
    """API view for updating cart item quantity - only for sales reps"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, item_id):
        if not request.user.is_sales_rep:
            return Response({'error': 'Cart access is only available for sales representatives'}, status=status.HTTP_403_FORBIDDEN)
        
        quantity = request.data.get('quantity')
        
        try:
            cart, created = Cart.objects.get_or_create(sales_rep=request.user)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.quantity = quantity
            cart_item.save()
            return Response({'message': 'Cart updated successfully'})
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)


# Pharmacist/Admin Order Management Views

class PharmacistOrderListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for pharmacist/admin to see all orders"""
    model = Order
    template_name = 'orders/pharmacist_order_list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.is_pharmacist_admin or self.request.user.is_admin
    
    def get_queryset(self):
        queryset = Order.objects.all().order_by('-created_at')
        
        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by payment status
        payment_filter = self.request.GET.get('payment_status')
        if payment_filter:
            queryset = queryset.filter(payment_status=payment_filter)
        
        # Filter by medicine
        medicine_filter = self.request.GET.get('medicine')
        if medicine_filter:
            queryset = queryset.filter(items__medicine_id=medicine_filter).distinct()
        
        # Search by order number or customer name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(order_number__icontains=search) |
                Q(customer_name__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from inventory.models import Medicine
        
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_status_choices'] = Order.PAYMENT_STATUS_CHOICES
        context['medicines'] = Medicine.objects.filter(is_active=True).order_by('name')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_payment_status'] = self.request.GET.get('payment_status', '')
        context['current_medicine'] = self.request.GET.get('medicine', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PharmacistOrderDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for pharmacist/admin to see order details"""
    model = Order
    template_name = 'orders/pharmacist_order_detail.html'
    context_object_name = 'order'
    
    def test_func(self):
        return self.request.user.is_pharmacist_admin or self.request.user.is_admin


class OrderStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for pharmacist/admin to update order status"""
    model = Order
    form_class = OrderStatusUpdateForm
    template_name = 'orders/order_status_update.html'
    
    def test_func(self):
        return self.request.user.is_pharmacist_admin or self.request.user.is_admin
    
    def get_success_url(self):
        return reverse_lazy('orders:pharmacist_order_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        # Add status history entry
        old_status = self.object.status
        old_payment_status = self.object.payment_status
        
        # Check stock availability before confirming order
        if (old_status == 'pending' and 
            form.cleaned_data.get('status') == 'confirmed'):
            
            is_available, message = self.object.check_stock_availability()
            if not is_available:
                messages.error(self.request, f'Cannot confirm order: {message}')
                return self.form_invalid(form)
        
        response = super().form_valid(form)
        
        # Create status history entry if status changed
        if old_status != self.object.status or old_payment_status != self.object.payment_status:
            from .models import OrderStatusHistory
            OrderStatusHistory.objects.create(
                order=self.object,
                old_status=old_status,
                new_status=self.object.status,
                old_payment_status=old_payment_status,
                new_payment_status=self.object.payment_status,
                notes=form.cleaned_data.get('internal_notes', ''),
                changed_by=self.request.user
            )
        
        # Handle timestamps for status changes
        if self.object.status == 'confirmed' and not self.object.confirmed_at:
            from django.utils import timezone
            self.object.confirmed_at = timezone.now()
            self.object.save()
        elif self.object.status == 'shipped' and not self.object.shipped_at:
            from django.utils import timezone
            self.object.shipped_at = timezone.now()
            self.object.save()
        elif self.object.status == 'delivered' and not self.object.delivered_at:
            from django.utils import timezone
            self.object.delivered_at = timezone.now()
            self.object.save()
        
        messages.success(self.request, f'Order status updated successfully.')
        return response


class OrderFulfillmentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard for pharmacist/admin order fulfillment"""
    template_name = 'orders/pharmacist_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_pharmacist_admin or self.request.user.is_admin
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status='pending').count()
        processing_orders = Order.objects.filter(status='processing').count()
        ready_orders = Order.objects.filter(status='ready_for_pickup').count()
        delivered_orders = Order.objects.filter(status='delivered').count()
        
        # Recent orders
        recent_orders = Order.objects.all().order_by('-created_at')[:10]
        
        # Orders by status
        orders_by_status = {}
        for status_code, status_name in Order.STATUS_CHOICES:
            orders_by_status[status_code] = {
                'name': status_name,
                'count': Order.objects.filter(status=status_code).count()
            }
        
        context.update({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'ready_orders': ready_orders,
            'delivered_orders': delivered_orders,
            'recent_orders': recent_orders,
            'orders_by_status': orders_by_status,
        })
        
        return context
