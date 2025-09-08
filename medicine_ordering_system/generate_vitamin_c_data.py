#!/usr/bin/env python
"""
Generate transactional time series data for Vitamin C 1000mg
Sales Rep: Ace
Period: 2000-2024 (25 years)
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

def create_vitamin_c_medicine():
    """Create Vitamin C 1000mg medicine record"""
    print("Creating Vitamin C 1000mg medicine record...")
    
    # Get or create category
    category, created = Category.objects.get_or_create(
        name="Vitamins & Supplements",
        defaults={'description': 'Vitamins, minerals, and dietary supplements'}
    )
    
    # Get or create manufacturer
    manufacturer, created = Manufacturer.objects.get_or_create(
        name="NutriHealth Corp",
        defaults={
            'country': 'United States',
            'contact_email': 'contact@nutrihealth.com',
            'contact_phone': '+1-555-0456',
            'website': 'https://www.nutrihealth.com'
        }
    )
    
    # Create Vitamin C medicine
    medicine, created = Medicine.objects.get_or_create(
        name="Vitamin C",
        defaults={
            'generic_name': 'Ascorbic Acid',
            'description': 'High-potency Vitamin C supplement for immune support and antioxidant protection',
            'category': category,
            'manufacturer': manufacturer,
            'dosage_form': 'Tablet',
            'strength': '1000mg',
            'prescription_type': 'otc',
            'unit_price': Decimal('8.99'),
            'cost_price': Decimal('3.50'),
            'current_stock': 5000,
            'minimum_stock_level': 200,
            'maximum_stock_level': 10000,
            'reorder_point': 500,
            'weight': Decimal('1.2'),
            'dimensions': '15x8x3mm',
            'storage_conditions': 'Store in cool, dry place away from light',
            'ndc_number': '54321-987-65',
            'fda_approval_date': date(1995, 6, 10),
            'expiry_date': date(2026, 12, 31),
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created new medicine: {medicine.name} {medicine.strength}")
    else:
        print(f"✅ Found existing medicine: {medicine.name} {medicine.strength}")
    
    return medicine

def create_sales_rep_ace():
    """Create sales rep Ace user account"""
    print("Creating sales rep Ace...")
    
    user, created = User.objects.get_or_create(
        username='ace_sales',
        defaults={
            'email': 'ace@medicineordering.com',
            'first_name': 'Ace',
            'last_name': 'Gutierrez',
            'role': 'sales_rep',
            'is_active': True,
            'is_staff': True
        }
    )
    
    if created:
        user.set_password('ace123456')
        user.save()
        print(f"✅ Created sales rep: {user.first_name} {user.last_name}")
    else:
        print(f"✅ Found existing sales rep: {user.first_name} {user.last_name}")
    
    return user

def create_customer_users():
    """Create diverse customer base for 25 years"""
    print("Creating customer base...")
    
    customers = []
    
    # Create customers with different profiles
    customer_profiles = [
        {'username': 'health_enthusiast', 'name': 'Health Enthusiast', 'email': 'health@example.com'},
        {'username': 'senior_citizen', 'name': 'Senior Citizen', 'email': 'senior@example.com'},
        {'username': 'fitness_trainer', 'name': 'Fitness Trainer', 'email': 'fitness@example.com'},
        {'username': 'busy_professional', 'name': 'Busy Professional', 'email': 'professional@example.com'},
        {'username': 'family_mom', 'name': 'Family Mom', 'email': 'mom@example.com'},
        {'username': 'college_student', 'name': 'College Student', 'email': 'student@example.com'},
        {'username': 'retiree', 'name': 'Retiree', 'email': 'retiree@example.com'},
        {'username': 'athlete', 'name': 'Athlete', 'email': 'athlete@example.com'},
        {'username': 'healthcare_worker', 'name': 'Healthcare Worker', 'email': 'healthcare@example.com'},
        {'username': 'wellness_coach', 'name': 'Wellness Coach', 'email': 'wellness@example.com'}
    ]
    
    for profile in customer_profiles:
        user, created = User.objects.get_or_create(
            username=profile['username'],
            defaults={
                'email': profile['email'],
                'first_name': profile['name'].split()[0],
                'last_name': profile['name'].split()[1] if len(profile['name'].split()) > 1 else 'Customer',
                'role': 'customer',
                'is_active': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
        customers.append(user)
    
    print(f"✅ Created/found {len(customers)} customers")
    return customers

def generate_25_year_sales_data(medicine, sales_rep, customers, start_year, end_year):
    """Generate realistic sales data spanning 25 years"""
    print(f"Generating sales data from {start_year} to {end_year}...")
    
    orders = []
    current_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    
    # Seasonal patterns for Vitamin C (higher in winter, flu season)
    seasonal_multipliers = {
        1: 1.4,  # January - peak cold/flu season
        2: 1.3,  # February - high cold season
        3: 1.1,  # March - transition
        4: 0.9,  # April - spring
        5: 0.8,  # May - spring
        6: 0.7,  # June - summer
        7: 0.6,  # July - summer
        8: 0.7,  # August - late summer
        9: 0.8,  # September - fall
        10: 0.9, # October - fall
        11: 1.2, # November - approaching winter
        12: 1.3  # December - winter
    }
    
    # Day of week patterns
    weekday_multipliers = {
        0: 0.9,  # Monday
        1: 1.0,  # Tuesday
        2: 1.0,  # Wednesday
        3: 1.0,  # Thursday
        4: 1.0,  # Friday
        5: 0.8,  # Saturday
        6: 0.6   # Sunday
    }
    
    # Growth trend over 25 years (gradual increase in health awareness)
    base_growth = 1.0
    year_growth_rate = 0.05  # 5% annual growth
    
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        weekday = current_date.weekday()
        
        # Calculate growth factor for this year
        years_from_start = year - start_year
        growth_factor = base_growth * (1 + year_growth_rate) ** years_from_start
        
        # Apply seasonal and weekday multipliers
        seasonal_mult = seasonal_multipliers.get(month, 1.0)
        weekday_mult = weekday_multipliers.get(weekday, 1.0)
        
        # Base daily sales (increases over time)
        base_orders = max(1, int(2 + years_from_start * 0.1))  # 2-4 orders per day
        daily_orders = max(1, int(base_orders * seasonal_mult * weekday_mult * growth_factor))
        
        # Generate orders for the day
        for _ in range(daily_orders):
            customer = random.choice(customers)
            
            # Order quantity (1-3 bottles, each bottle has 60 tablets)
            quantity = random.randint(1, 3) * 60
            
            # Create order
            order_number = f"VC{current_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            # Ensure unique order number
            while Order.objects.filter(order_number=order_number).exists():
                order_number = f"VC{current_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            order = Order.objects.create(
                order_number=order_number,
                sales_rep=sales_rep,
                customer_name=f"{customer.first_name} {customer.last_name}",
                customer_phone="+1-555-0123",
                customer_address="123 Main St, City, State 12345",
                status='delivered',
                payment_status='paid',
                subtotal=medicine.unit_price * quantity,
                total_amount=medicine.unit_price * quantity,
                delivery_method='delivery',
                created_at=datetime.combine(current_date, datetime.min.time()),
                confirmed_at=datetime.combine(current_date, datetime.min.time()) + timedelta(hours=1),
                shipped_at=datetime.combine(current_date, datetime.min.time()) + timedelta(hours=2),
                delivered_at=datetime.combine(current_date, datetime.min.time()) + timedelta(hours=4),
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
    
    print(f"✅ Generated {len(orders)} orders over {end_year - start_year + 1} years")
    return orders

def create_analytics_data(medicine, orders):
    """Create comprehensive analytics data"""
    print("Creating analytics data...")
    
    # Group orders by year and month for trend analysis
    yearly_sales = {}
    monthly_sales = {}
    
    for order in orders:
        year = order.created_at.year
        month_key = order.created_at.strftime('%Y-%m')
        
        if year not in yearly_sales:
            yearly_sales[year] = {'quantity': 0, 'revenue': 0, 'orders': 0}
        if month_key not in monthly_sales:
            monthly_sales[month_key] = {'quantity': 0, 'revenue': 0, 'orders': 0}
        
        order_item = order.items.filter(medicine=medicine).first()
        if order_item:
            yearly_sales[year]['quantity'] += order_item.quantity
            yearly_sales[year]['revenue'] += float(order_item.total_price)
            yearly_sales[year]['orders'] += 1
            
            monthly_sales[month_key]['quantity'] += order_item.quantity
            monthly_sales[month_key]['revenue'] += float(order_item.total_price)
            monthly_sales[month_key]['orders'] += 1
    
    # Create yearly sales trends
    for year, data in yearly_sales.items():
        SalesTrend.objects.create(
            medicine=medicine,
            period_type='yearly',
            period_date=date(year, 12, 31),  # End of year
            quantity_sold=data['quantity'],
            revenue=Decimal(str(data['revenue'])),
            average_price=Decimal(str(data['revenue'] / data['quantity'])) if data['quantity'] > 0 else Decimal('0'),
            trend_direction='up' if year >= 2015 else 'stable'
        )
    
    # Create monthly sales trends for recent years
    recent_months = [month for month in monthly_sales.keys() if month.startswith('202')]
    for month_key in recent_months:
        data = monthly_sales[month_key]
        year, month = month_key.split('-')
        period_date = date(int(year), int(month), 1)
        SalesTrend.objects.create(
            medicine=medicine,
            period_type='monthly',
            period_date=period_date,
            quantity_sold=data['quantity'],
            revenue=Decimal(str(data['revenue'])),
            average_price=Decimal(str(data['revenue'] / data['quantity'])) if data['quantity'] > 0 else Decimal('0'),
            trend_direction='up' if data['quantity'] > 1000 else 'stable'
        )
    
    # Create demand forecasts for different periods
    recent_quantity = sum(data['quantity'] for year, data in yearly_sales.items() if year >= 2020)
    recent_years = len([year for year in yearly_sales.keys() if year >= 2020])
    average_yearly = recent_quantity / recent_years if recent_years > 0 else 0
    
    # Annual forecast
    DemandForecast.objects.create(
        medicine=medicine,
        forecast_period='yearly',
        predicted_quantity=int(average_yearly * 1.08),  # 8% growth
        confidence_level=0.90,
        forecast_date=timezone.now(),
        created_at=timezone.now()
    )
    
    # Monthly forecast
    DemandForecast.objects.create(
        medicine=medicine,
        forecast_period='monthly',
        predicted_quantity=int(average_yearly / 12 * 1.05),  # 5% growth
        confidence_level=0.85,
        forecast_date=timezone.now(),
        created_at=timezone.now()
    )
    
    print("✅ Created comprehensive analytics data")

def main():
    """Main function to generate all data"""
    print("=== VITAMIN C 1000MG TIME SERIES DATA GENERATION ===")
    print("Sales Rep: Ace Gutierrez")
    print("Period: 2000-2024 (25 years)")
    print()
    
    # Create medicine
    medicine = create_vitamin_c_medicine()
    print()
    
    # Create sales rep
    sales_rep = create_sales_rep_ace()
    print()
    
    # Create customers
    customers = create_customer_users()
    print()
    
    # Generate sales data for 25 years
    start_year = 2000
    end_year = 2024
    orders = generate_25_year_sales_data(medicine, sales_rep, customers, start_year, end_year)
    print()
    
    # Create analytics data
    create_analytics_data(medicine, orders)
    print()
    
    print("=== DATA GENERATION COMPLETE ===")
    print(f"✅ Medicine: {medicine.name} {medicine.strength}")
    print(f"✅ Sales Rep: {sales_rep.first_name} {sales_rep.last_name}")
    print(f"✅ Total Orders: {len(orders)}")
    print(f"✅ Date Range: {start_year} to {end_year} ({end_year - start_year + 1} years)")
    print(f"✅ Total Quantity Sold: {sum(item.quantity for order in orders for item in order.items.filter(medicine=medicine))}")
    print(f"✅ Total Revenue: ${sum(float(item.total_price) for order in orders for item in order.items.filter(medicine=medicine)):.2f}")

if __name__ == "__main__":
    main()
