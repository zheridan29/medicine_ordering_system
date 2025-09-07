from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as BaseLoginView
from django.contrib.auth.views import LogoutView as BaseLogoutView
from django.contrib.auth.views import PasswordResetView as BasePasswordResetView
from django.contrib.auth.views import PasswordResetConfirmView as BasePasswordResetConfirmView
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, RedirectView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .models import User, SalesRepProfile, PharmacistAdminProfile
from .forms import UserRegistrationForm, ProfileEditForm, UserEditForm


class LoginView(BaseLoginView):
    """Custom login view"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if user.is_admin:
            return reverse('oncare_admin:dashboard')
        elif user.is_pharmacist_admin:
            return reverse('inventory:dashboard')
        else:  # Sales Representative
            return reverse('orders:dashboard')


class LogoutConfirmView(TemplateView):
    """Logout confirmation view"""
    template_name = 'accounts/logout_confirm.html'

class LogoutView(TemplateView):
    """Custom logout view that handles both GET and POST"""
    template_name = 'accounts/logout.html'
    
    def get(self, request, *args, **kwargs):
        # Handle GET request - show logout page
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        # Handle POST request - perform logout
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been successfully logged out. Thank you for using OnCare!')
        return redirect('home')


class RegisterView(CreateView):
    """User registration view"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Registration successful! Please log in.')
        return response


class PasswordResetView(BasePasswordResetView):
    """Password reset view"""
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    """Password reset confirm view"""
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view"""
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self):
        return self.request.user


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Profile edit view"""
    model = User
    form_class = ProfileEditForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Remove the request parameter as it's not needed for ProfileEditForm
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class UserListView(LoginRequiredMixin, ListView):
    """User list view (admin only)"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()
        
        queryset = User.objects.all()
        search = self.request.GET.get('search')
        role = self.request.GET.get('role')
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_choices'] = User.ROLE_CHOICES
        return context


class UserDetailView(LoginRequiredMixin, DetailView):
    """User detail view (admin only)"""
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user_detail'
    
    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()
        return User.objects.all()


class UserEditView(LoginRequiredMixin, UpdateView):
    """User edit view (admin only)"""
    model = User
    form_class = UserEditForm
    template_name = 'accounts/user_edit.html'
    
    def get_queryset(self):
        if not self.request.user.is_admin:
            return User.objects.none()
        return User.objects.all()
    
    def get_success_url(self):
        return reverse('accounts:user_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'User updated successfully!')
        return super().form_valid(form)


# API Views
class ProfileAPIView(APIView):
    """Profile API view"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'phone_number': user.phone_number,
            'address': user.address,
            'city': user.city,
            'state': user.state,
            'zip_code': user.zip_code,
            'country': user.country,
            'is_verified': user.is_verified,
            'date_joined': user.date_joined,
        })
    
    def put(self, request):
        user = request.user
        data = request.data
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'phone_number', 'address', 'city', 'state', 'zip_code', 'country']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'phone_number': user.phone_number,
                'address': user.address,
                'city': user.city,
                'state': user.state,
                'zip_code': user.zip_code,
                'country': user.country,
            }
        })


class UserListAPIView(APIView):
    """User list API view (admin only)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_admin:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all()
        search = request.GET.get('search')
        role = request.GET.get('role')
        
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        if role:
            users = users.filter(role=role)
        
        # Pagination
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        paginator = Paginator(users, per_page)
        page_obj = paginator.get_page(page)
        
        users_data = []
        for user in page_obj:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_verified': user.is_verified,
                'date_joined': user.date_joined,
            })
        
        return Response({
            'users': users_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': paginator.num_pages,
                'total_count': paginator.count,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })