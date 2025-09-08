#!/usr/bin/env python
"""
Generate historical transactional data using direct SQL insertion
This bypasses Django's timezone handling for guaranteed historical dates
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import sqlite3

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from django.db import connection
from inventory.models import Medicine
from accounts.models import User

def get_database_path():
    """Get the SQLite database path"""
    from django.conf import settings
    return settings.DATABASES['default']['NAME']

def create_historical_orders_sql(medicine_id, sales_rep_id, customer_ids, start_year, end_year):
    """Create historical orders using direct SQL"""
    
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"Creating historical orders from {start_year} to {end_year}...")
    
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
    
    orders_created = 0
    current_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    
    # Growth trend over years (gradual increase in health awareness)
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
            customer_id = random.choice(customer_ids)
            
            # Order quantity (1-3 bottles, each bottle has 60 tablets)
            quantity = random.randint(1, 3) * 60
            unit_price = 8.99  # Vitamin C price
            total_amount = unit_price * quantity
            
            # Create order with historical date
            order_number = f"VC{current_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            # Insert order with proper historical datetime
            order_datetime = datetime.combine(current_date, datetime.min.time())
            confirmed_datetime = order_datetime + timedelta(hours=1)
            shipped_datetime = order_datetime + timedelta(hours=2)
            delivered_datetime = order_datetime + timedelta(hours=4)
            
            cursor.execute("""
                INSERT INTO orders_order (
                    order_number, sales_rep_id, customer_name, customer_phone, customer_address,
                    status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
                    delivery_method, delivery_address, created_at, confirmed_at, shipped_at, delivered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_number, sales_rep_id, f"Customer {customer_id}", "+1-555-0123", "123 Main St, City, State 12345",
                'delivered', 'paid', total_amount, 0.0, 0.0, 0.0, total_amount,
                'delivery', "123 Main St, City, State 12345", order_datetime, confirmed_datetime, shipped_datetime, delivered_datetime
            ))
            
            order_id = cursor.lastrowid
            
            # Insert order item
            cursor.execute("""
                INSERT INTO orders_orderitem (
                    order_id, medicine_id, quantity, unit_price, total_price
                ) VALUES (?, ?, ?, ?, ?)
            """, (order_id, medicine_id, quantity, unit_price, total_amount))
            
            orders_created += 1
        
        current_date += timedelta(days=1)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created {orders_created} orders with historical dates")
    return orders_created

def main():
    """Main function to generate historical data"""
    print("=== HISTORICAL DATA GENERATION (SQL) ===")
    print("Using direct SQL insertion for guaranteed historical dates")
    print()
    
    # Get Vitamin C medicine
    try:
        vitamin_c = Medicine.objects.get(name='Vitamin C')
        print(f"✅ Found medicine: {vitamin_c.name} {vitamin_c.strength} (ID: {vitamin_c.id})")
    except Medicine.DoesNotExist:
        print("❌ Vitamin C medicine not found. Please run the regular generation script first.")
        return
    
    # Get sales rep
    try:
        sales_rep = User.objects.get(username='ace_sales')
        print(f"✅ Found sales rep: {sales_rep.first_name} {sales_rep.last_name} (ID: {sales_rep.id})")
    except User.DoesNotExist:
        print("❌ Sales rep ace_sales not found. Please run the regular generation script first.")
        return
    
    # Get customer IDs
    customers = User.objects.filter(role='customer')
    customer_ids = [c.id for c in customers]
    print(f"✅ Found {len(customer_ids)} customers")
    print()
    
    # Clear existing Vitamin C data
    print("Clearing existing Vitamin C data...")
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM orders_orderitem WHERE medicine_id = %s", [vitamin_c.id])
        cursor.execute("DELETE FROM orders_order WHERE id IN (SELECT order_id FROM orders_orderitem WHERE medicine_id = %s)", [vitamin_c.id])
        cursor.execute("DELETE FROM analytics_salestrend WHERE medicine_id = %s", [vitamin_c.id])
        cursor.execute("DELETE FROM analytics_demandforecast WHERE medicine_id = %s", [vitamin_c.id])
    print("✅ Data cleared")
    print()
    
    # Generate historical data
    start_year = 2000
    end_year = 2024
    
    orders_created = create_historical_orders_sql(
        vitamin_c.id, 
        sales_rep.id, 
        customer_ids, 
        start_year, 
        end_year
    )
    
    print()
    print("=== VERIFICATION ===")
    
    # Verify the data
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as order_count,
                   MIN(created_at) as first_order,
                   MAX(created_at) as last_order,
                   SUM(oi.quantity) as total_quantity,
                   SUM(oi.total_price) as total_revenue
            FROM orders_order o
            JOIN orders_orderitem oi ON o.id = oi.order_id
            WHERE oi.medicine_id = %s
        """, [vitamin_c.id])
        
        result = cursor.fetchone()
        order_count, first_order, last_order, total_quantity, total_revenue = result
        
        print(f"✅ Total Orders: {order_count:,}")
        print(f"✅ Date Range: {first_order[:10]} to {last_order[:10]}")
        print(f"✅ Total Quantity: {total_quantity:,} units")
        print(f"✅ Total Revenue: ${total_revenue:,.2f}")
    
    print()
    print("=== HISTORICAL DATA GENERATION COMPLETE ===")
    print("✅ All dates are now properly historical (2000-2024)")
    print("✅ No timezone conversion issues")
    print("✅ Ready for forecasting and analytics")

if __name__ == "__main__":
    main()
