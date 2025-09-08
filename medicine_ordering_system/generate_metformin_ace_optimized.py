#!/usr/bin/env python3
"""
Optimized Metformin Historical Data Generator for Sales Rep "ace" (2015-2025)
Designed for maximum ARIMA forecasting accuracy with 10 years of dense data
"""

import os
import sys
import django
import random
import sqlite3
from datetime import datetime, timedelta, date
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from inventory.models import Medicine, StockMovement
from orders.models import Order, OrderItem, OrderStatusHistory

User = get_user_model()

def get_database_path():
    """Get the SQLite database path"""
    from django.conf import settings
    return settings.DATABASES['default']['NAME']

def get_ace_sales_rep():
    """Get the sales representative with username 'ace'"""
    db_path = get_database_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id FROM accounts_user 
            WHERE username = 'ace' AND role IN ('sales_rep', 'pharmacist_admin', 'admin')
        """)
        ace_user = cursor.fetchone()
        if not ace_user:
            raise Exception("Sales rep 'ace' not found. Please create this user first.")
        
        return ace_user[0]
        
    except Exception as e:
        print(f"Error getting ace sales rep: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_next_stock_movement_id():
    """Get next available stock movement ID"""
    db_path = get_database_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM inventory_stockmovement")
        max_id = cursor.fetchone()[0] or 0
        return max_id + 1
    except Exception as e:
        print(f"Error getting stock movement ID: {e}")
        return random.randint(10000, 99999)
    finally:
        if conn:
            conn.close()

def calculate_optimized_daily_sales(current_date, start_date):
    """Calculate optimized daily sales for Metformin (diabetes medication)"""
    # Base sales for diabetes medication (higher for more data points)
    base_sales = 35  # Higher than Amoxicillin due to chronic condition
    
    # Seasonal patterns for diabetes medication (higher in winter months)
    month = current_date.month
    if month in [12, 1, 2]:  # Winter - higher diabetes management
        seasonal_mult = 1.6
    elif month in [6, 7, 8]:  # Summer - lower demand
        seasonal_mult = 0.8
    elif month in [3, 4, 5]:  # Spring - moderate
        seasonal_mult = 1.1
    else:  # Fall - moderate
        seasonal_mult = 1.2
    
    # Weekday patterns (more variation for better patterns)
    weekday = current_date.weekday()
    if weekday == 6:  # Sunday
        weekday_mult = 0.6
    elif weekday == 5:  # Saturday
        weekday_mult = 0.9
    elif weekday in [0, 1, 2, 3, 4]:  # Weekdays
        weekday_mult = 1.3
    else:
        weekday_mult = 1.0
    
    # Growth trend (more realistic business growth for diabetes medication)
    years_elapsed = (current_date - start_date).days / 365.25
    growth_factor = (1 + 0.14) ** years_elapsed  # 14% annual growth (higher than Amoxicillin)
    
    # Random variation (more realistic)
    random_factor = random.uniform(0.7, 1.3)
    
    # Calculate final sales
    daily_sales = int(base_sales * seasonal_mult * weekday_mult * growth_factor * random_factor)
    
    # Ensure minimum sales for data density
    return max(10, daily_sales)  # Minimum 10 sales per day

def generate_metformin_ace_optimized():
    print("=== Optimized Metformin Data Generator for Sales Rep 'ace' ===")
    print("Creating 10 years of dense data (2015-2025) for maximum forecasting accuracy")
    
    # 1. Get medicine
    try:
        metformin = Medicine.objects.get(id=4)  # Metformin 500mg
        print(f"✅ Found medicine: {metformin.name}")
    except Medicine.DoesNotExist:
        print("❌ Metformin not found in inventory. Please run generate_medicines.py first.")
        return

    # 2. Get ace sales rep
    ace_sales_rep_id = get_ace_sales_rep()
    if not ace_sales_rep_id:
        print("❌ Sales rep 'ace' not available")
        return
    print(f"✅ Found sales rep 'ace' (ID: {ace_sales_rep_id})")

    # 3. Clear existing data for medicine 4
    print("\n🧹 Clearing existing data...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM orders_orderitem WHERE medicine_id = 4")
            cursor.execute("DELETE FROM orders_orderstatushistory WHERE order_id IN (SELECT id FROM orders_order WHERE sales_rep_id = %s)", [ace_sales_rep_id])
            cursor.execute("DELETE FROM orders_order WHERE sales_rep_id = %s", [ace_sales_rep_id])
            cursor.execute("DELETE FROM inventory_stockmovement WHERE medicine_id = 4")
            print("✅ Cleared existing data")
    except Exception as e:
        print(f"⚠️  Error clearing data: {e}")

    # 4. Define optimized date range (2015-2025) - 10 years for maximum accuracy
    start_date = date(2015, 1, 1)
    end_date = date(2025, 12, 31)
    
    # 5. Generate optimized orders
    current_date = start_date
    orders_created = 0
    current_stock = 12000  # Higher initial stock for 10 years
    stock_movement_id = get_next_stock_movement_id()
    order_counter = 0
    random.seed(42)  # for reproducibility

    print(f"\n📅 Generating optimized orders from {start_date} to {end_date}")
    print(f"   Target: ~36,500+ daily data points for maximum accuracy")
    
    db_path = get_database_path()
    conn = None
    
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        print(f"📊 Starting optimized data generation...")
        print(f"   Database: {db_path}")
        print(f"   Sales rep: ace (ID: {ace_sales_rep_id})")
        
        while current_date <= end_date:
            # Calculate optimized daily sales
            daily_sales = calculate_optimized_daily_sales(current_date, start_date)
            
            # Check if we need to reorder (more frequent reorders for realism)
            if current_stock < daily_sales and current_stock <= 500:
                reorder_qty = 2500  # Larger reorder quantity for Metformin
                current_stock += reorder_qty
                
                # Create stock movement for reorder
                cursor.execute("""
                    INSERT INTO inventory_stockmovement 
                    (id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_movement_id,
                    4,  # Metformin ID
                    'in',
                    reorder_qty,
                    f"ACE-REORDER-{current_date.strftime('%Y%m%d')}",
                    f"Reorder by ace - stock below reorder point",
                    ace_sales_rep_id,
                    current_date.isoformat()
                ))
                stock_movement_id += 1
            
            # Create optimized orders for the day (more orders per day)
            orders_today = min(max(3, daily_sales // 3), 18)  # 3-18 orders per day
            remaining_sales = daily_sales
            
            for order_num in range(orders_today):
                if remaining_sales <= 0 or current_stock <= 0:
                    break
                
                order_qty = min(random.randint(1, 10), remaining_sales, current_stock)  # Larger quantities
                if order_qty <= 0:
                    break
                
                # Safety check to prevent excessive data
                if orders_created > 60000:  # Max 60k orders for 10 years
                    print(f"⚠️  Reached maximum order limit (60,000). Stopping generation.")
                    break
                
                # Create order
                order_counter += 1
                order_number = f"MET-{current_date.strftime('%Y%m%d')}{order_counter:04d}"
                
                # Create order record (ace creates order with customer details)
                cursor.execute("""
                    INSERT INTO orders_order 
                    (order_number, sales_rep_id, customer_name, customer_phone, customer_address, 
                     status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount, 
                     total_amount, delivery_method, delivery_address, delivery_instructions, 
                     prescription_required, prescription_verified, customer_notes, internal_notes, 
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_number,
                    ace_sales_rep_id,
                    f"Customer-{order_counter:08d}",  # ace assigned customer name
                    f"555-{order_counter:05d}",      # ace assigned phone
                    f"Delivery Address {order_counter}",  # ace assigned address
                    'delivered',
                    'paid',
                    order_qty * float(metformin.unit_price),  # subtotal
                    0.00,  # tax_amount
                    0.00,  # shipping_cost
                    0.00,  # discount_amount
                    order_qty * float(metformin.unit_price),  # total_amount
                    'delivery',  # delivery_method
                    f"Delivery Address {order_counter}",
                    "Standard delivery by ace",
                    False,  # prescription_required
                    True,   # prescription_verified
                    f"Customer notes for order {order_number}",  # customer_notes
                    f"Order created by ace - {order_number}",  # internal_notes
                    current_date.isoformat(),
                    current_date.isoformat()
                ))
                
                order_id = cursor.lastrowid
                
                # Create order item
                cursor.execute("""
                    INSERT INTO orders_orderitem 
                    (order_id, medicine_id, quantity, unit_price, total_price, 
                     prescription_notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    4,  # Metformin ID
                    order_qty,
                    float(metformin.unit_price),
                    order_qty * float(metformin.unit_price),
                    f"Prescription for {metformin.name} - processed by ace",
                    current_date.isoformat()
                ))
                
                # Create order status history
                cursor.execute("""
                    INSERT INTO orders_orderstatushistory 
                    (order_id, old_status, new_status, old_payment_status, new_payment_status, 
                     notes, changed_by_id, changed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    'pending',  # old_status
                    'delivered',  # new_status
                    'pending',  # old_payment_status
                    'paid',  # new_payment_status
                    'Order completed successfully by ace',
                    ace_sales_rep_id,
                    current_date.isoformat()
                ))
                
                # Update stock
                current_stock -= order_qty
                remaining_sales -= order_qty
                orders_created += 1
                
                # Create stock movement for sale
                cursor.execute("""
                    INSERT INTO inventory_stockmovement 
                    (id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_movement_id,
                    4,  # Metformin ID
                    'out',
                    -order_qty,
                    order_number,
                    f"Sale by ace - Order {order_number}",
                    ace_sales_rep_id,
                    current_date.isoformat()
                ))
                stock_movement_id += 1
            
            # Break outer loop if we hit the limit
            if orders_created > 60000:
                break
            
            # Progress reporting (monthly)
            if current_date.day == 1:  # Monthly progress
                print(f"  📅 {current_date.strftime('%Y-%m')}: {orders_created} orders, Stock: {current_stock}")
            
            current_date += timedelta(days=1)
        
        # Update medicine stock
        cursor.execute("""
            UPDATE inventory_medicine 
            SET current_stock = ? 
            WHERE id = ?
        """, (current_stock, 4))
        
        conn.commit()
        print(f"\n✅ Generated {orders_created} orders for {metformin.name}")
        print(f"   Final stock: {current_stock}")
        print(f"   Date range: {start_date} to {end_date}")
        print(f"   All orders created by sales rep: ace")
        
        # Verify data was inserted
        cursor.execute("SELECT COUNT(*) FROM orders_orderitem WHERE medicine_id = 4")
        count = cursor.fetchone()[0]
        print(f"   Verified: {count} order items in database")
        
    except Exception as e:
        print(f"❌ Error creating orders: {e}")
        import traceback
        traceback.print_exc()
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def verify_optimized_data_quality():
    """Verify the optimized data quality for maximum forecasting accuracy"""
    print("\n=== Optimized Data Quality Verification ===")
    
    try:
        from analytics.services import ARIMAForecastingService
        service = ARIMAForecastingService()
        
        for period_type in ['daily', 'weekly', 'monthly']:
            try:
                data = service.prepare_sales_data(4, period_type)  # Medicine ID 4
                non_zero = (data['quantity'] > 0).sum()
                total = len(data)
                
                print(f"{period_type.upper()} Data:")
                print(f"  Total periods: {total}")
                print(f"  Non-zero periods: {non_zero} ({non_zero/total*100:.1f}%)")
                print(f"  Min quantity: {data['quantity'].min()}")
                print(f"  Max quantity: {data['quantity'].max()}")
                print(f"  Mean quantity: {data['quantity'].mean():.2f}")
                print(f"  Std quantity: {data['quantity'].std():.2f}")
                
                # Enhanced accuracy requirements
                if period_type == 'daily' and non_zero >= 3650:  # 10+ years
                    print(f"  ✅ Excellent data density for {period_type} forecasting (10+ years)")
                elif period_type == 'weekly' and non_zero >= 520:  # 10+ years
                    print(f"  ✅ Excellent data density for {period_type} forecasting (10+ years)")
                elif period_type == 'monthly' and non_zero >= 120:  # 10+ years
                    print(f"  ✅ Excellent data density for {period_type} forecasting (10+ years)")
                elif non_zero >= service.min_data_points.get(period_type, 30):
                    print(f"  ✅ Sufficient data for {period_type} forecasting")
                else:
                    print(f"  ⚠️  Insufficient data for {period_type} forecasting")
                
            except Exception as e:
                print(f"  ❌ Error verifying {period_type} data: {e}")
    
    except Exception as e:
        print(f"❌ Error in verification: {e}")

def test_optimized_forecasting():
    """Test forecasting with the optimized data"""
    print("\n=== Testing Optimized Forecasting ===")
    
    try:
        from analytics.services import ARIMAForecastingService
        service = ARIMAForecastingService()
        
        # Test weekly forecast
        try:
            forecast = service.generate_forecast(4, 'weekly', 8)  # 8 weeks ahead
            print(f"✅ Weekly forecast successful:")
            print(f"   Forecast: {[round(x, 2) for x in forecast.forecasted_demand]}")
            print(f"   Data points: {forecast.training_data_points}")
            print(f"   ARIMA params: p={forecast.arima_p}, d={forecast.arima_d}, q={forecast.arima_q}")
        except Exception as e:
            print(f"❌ Weekly forecast failed: {e}")
        
        # Test monthly forecast
        try:
            forecast = service.generate_forecast(4, 'monthly', 6)  # 6 months ahead
            print(f"✅ Monthly forecast successful:")
            print(f"   Forecast: {[round(x, 2) for x in forecast.forecasted_demand]}")
            print(f"   Data points: {forecast.training_data_points}")
        except Exception as e:
            print(f"❌ Monthly forecast failed: {e}")
            
    except Exception as e:
        print(f"❌ Error testing forecasting: {e}")

if __name__ == "__main__":
    generate_metformin_ace_optimized()
    
    # Verify optimized data quality
    verify_optimized_data_quality()
    
    # Test optimized forecasting
    test_optimized_forecasting()
    
    print("\n🎉 Optimized Metformin data generation completed!")
    print("   The data is now optimized for maximum ARIMA forecasting accuracy.")
    print("   All transactions created by sales rep: ace")
    print("   Data spans 10 years (2015-2025) for superior pattern recognition.")