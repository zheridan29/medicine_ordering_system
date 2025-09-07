#!/usr/bin/env python
"""
Generate transactional time series data for Paracetamol
Based on SYSTEM_ANALYSIS_REPORT and DATABASE_AND_MODELS_ANALYSIS
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import json
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from inventory.models import Category, Manufacturer, Medicine
from orders.models import Order, OrderItem
from analytics.models import SalesTrend, DemandForecast, CustomerAnalytics
from accounts.models import User

def create_paracetamol_medicine():
    """Create Paracetamol medicine record"""
    print("Creating Paracetamol medicine record...")
    
    # Get or create category
    category, created = Category.objects.get_or_create(
        name="Pain Relief",
        defaults={'description': 'Pain relief and fever reduction medications'}
    )
    
    # Get or create manufacturer
    manufacturer, created = Manufacturer.objects.get_or_create(
        name="Generic Pharma Inc.",
        defaults={
            'contact_person': 'John Smith',
            'email': 'contact@genericpharma.com',
            'phone': '+1-555-0123',
            'address': '123 Pharma Street, Medicine City, MC 12345'
        }
    )
    
    # Create Paracetamol medicine
    medicine, created = Medicine.objects.get_or_create(
        name="Paracetamol",
        defaults={
            'generic_name': 'Acetaminophen',
            'description': 'Pain relief and fever reduction medication',
            'category': category,
            'manufacturer': manufacturer,
            'dosage_form': 'Tablet',
            'strength': '500mg',
            'prescription_type': 'otc',
            'unit_price': Decimal('2.50'),
            'cost_price': Decimal('1.20'),
            'current_stock': 1000,
            'minimum_stock_level': 50,
            'maximum_stock_level': 2000,
            'reorder_point': 100,
            'weight': Decimal('0.5'),
            'dimensions': '10x5x2mm',
            'storage_conditions': 'Store at room temperature',
            'ndc_number': '12345-678-90',
            'fda_approval_date': date(2018, 1, 15),
            'expiry_date': date(2025, 12, 31),
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created new medicine: {medicine.name}")
    else:
        print(f"✅ Found existing medicine: {medicine.name}")
    
    return medicine

def create_test_users():
    """Create test users for orders"""
    print("Creating test users...")
    
    users = []
    for i in range(1, 6):
        user, created = User.objects.get_or_create(
            username=f'customer{i}',
            defaults={
                'email': f'customer{i}@example.com',
                'first_name': f'Customer{i}',
                'last_name': 'Test',
                'role': 'customer',
                'is_active': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        users.append(user)
    
    print(f"✅ Created/found {len(users)} test users")
    return users

def generate_seasonal_sales_data(medicine, users, start_date, end_date):
    """Generate realistic seasonal sales data"""
    print(f"Generating sales data from {start_date} to {end_date}...")
    
    orders = []
    current_date = start_date
    
    # Seasonal multipliers (higher in winter for cold/flu season)
    seasonal_multipliers = {
        1: 1.3,  # January - peak cold season
        2: 1.2,  # February - high cold season
        3: 0.9,  # March - transition
        4: 0.8,  # April - low season
        5: 0.7,  # May - low season
        6: 0.6,  # June - low season
        7: 0.6,  # July - low season
        8: 0.7,  # August - low season
        9: 0.8,  # September - transition
        10: 0.9, # October - transition
        11: 1.1, # November - increasing
        12: 1.2  # December - high season
    }
    
    # Day of week multipliers (higher on weekdays)
    weekday_multipliers = {
        0: 0.8,  # Monday
        1: 1.0,  # Tuesday
        2: 1.0,  # Wednesday
        3: 1.0,  # Thursday
        4: 1.0,  # Friday
        5: 0.6,  # Saturday
        6: 0.4   # Sunday
    }
    
    while current_date <= end_date:
        # Calculate base sales for the day
        month = current_date.month
        weekday = current_date.weekday()
        
        seasonal_mult = seasonal_multipliers.get(month, 1.0)
        weekday_mult = weekday_multipliers.get(weekday, 1.0)
        
        # Base daily sales (1-3 orders per day)
        base_orders = random.randint(1, 3)
        daily_orders = max(1, int(base_orders * seasonal_mult * weekday_mult))
        
        # Generate orders for the day
        for _ in range(daily_orders):
            user = random.choice(users)
            
            # Order quantity (1-5 boxes, each box has 20 tablets)
            quantity = random.randint(1, 5) * 20
            
            # Create order
            order = Order.objects.create(
                customer=user,
                status='delivered',
                payment_status='completed',
                total_amount=medicine.unit_price * quantity,
                shipping_address=f"{user.first_name} {user.last_name}, 123 Main St, City, State 12345",
                billing_address=f"{user.first_name} {user.last_name}, 123 Main St, City, State 12345",
                created_at=timezone.datetime.combine(current_date, datetime.min.time()),
                confirmed_at=timezone.datetime.combine(current_date, datetime.min.time()) + timedelta(hours=1),
                shipped_at=timezone.datetime.combine(current_date, datetime.min.time()) + timedelta(hours=2),
                delivered_at=timezone.datetime.combine(current_date, datetime.min.time()) + timedelta(hours=4),
            )
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                medicine=medicine,
                quantity=quantity,
                unit_price=medicine.unit_price,
                total_price=medicine.unit_price * quantity
            )
            
            orders.append(order)
        
        current_date += timedelta(days=1)
    
    print(f"✅ Generated {len(orders)} orders")
    return orders

def create_analytics_data(medicine, orders):
    """Create analytics and trend data"""
    print("Creating analytics data...")
    
    # Group orders by month for trend analysis
    monthly_sales = {}
    for order in orders:
        month_key = order.created_at.strftime('%Y-%m')
        if month_key not in monthly_sales:
            monthly_sales[month_key] = {'quantity': 0, 'revenue': 0, 'orders': 0}
        
        order_item = order.items.filter(medicine=medicine).first()
        if order_item:
            monthly_sales[month_key]['quantity'] += order_item.quantity
            monthly_sales[month_key]['revenue'] += float(order_item.total_price)
            monthly_sales[month_key]['orders'] += 1
    
    # Create sales trends
    for month_key, data in monthly_sales.items():
        SalesTrend.objects.create(
            medicine=medicine,
            period=month_key,
            total_quantity_sold=data['quantity'],
            total_revenue=Decimal(str(data['revenue'])),
            average_order_value=Decimal(str(data['revenue'] / data['orders'])) if data['orders'] > 0 else Decimal('0'),
            trend_direction='up' if data['quantity'] > 1000 else 'stable',
            created_at=timezone.now()
        )
    
    # Create demand forecast (simplified)
    total_quantity = sum(data['quantity'] for data in monthly_sales.values())
    average_monthly = total_quantity / len(monthly_sales) if monthly_sales else 0
    
    DemandForecast.objects.create(
        medicine=medicine,
        forecast_period='monthly',
        predicted_quantity=int(average_monthly * 1.1),  # 10% growth
        confidence_level=0.85,
        forecast_date=timezone.now(),
        created_at=timezone.now()
    )
    
    print("✅ Created analytics data")

def main():
    """Main function to generate all data"""
    print("=== PARACETAMOL TIME SERIES DATA GENERATION ===")
    print()
    
    # Create medicine
    medicine = create_paracetamol_medicine()
    print()
    
    # Create test users
    users = create_test_users()
    print()
    
    # Generate sales data for 2020
    start_date = date(2020, 1, 1)
    end_date = date(2020, 12, 31)
    orders = generate_seasonal_sales_data(medicine, users, start_date, end_date)
    print()
    
    # Create analytics data
    create_analytics_data(medicine, orders)
    print()
    
    print("=== DATA GENERATION COMPLETE ===")
    print(f"✅ Medicine: {medicine.name} ({medicine.strength})")
    print(f"✅ Total Orders: {len(orders)}")
    print(f"✅ Date Range: {start_date} to {end_date}")
    print(f"✅ Total Quantity Sold: {sum(item.quantity for order in orders for item in order.items.filter(medicine=medicine))}")
    print(f"✅ Total Revenue: ${sum(float(item.total_price) for order in orders for item in order.items.filter(medicine=medicine)):.2f}")

if __name__ == "__main__":
    main()
