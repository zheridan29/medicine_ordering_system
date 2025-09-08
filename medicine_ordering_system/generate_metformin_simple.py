#!/usr/bin/env python3
"""
Simple Metformin Historical Data Generator for Sales Rep "ace" (2000-2025)
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
from inventory.models import Medicine

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

def calculate_daily_sales(current_date, start_date):
    """Calculate daily sales for Metformin"""
    # Base sales for diabetes medication
    base_sales = 30
    
    # Seasonal patterns (diabetes medication - higher in winter months)
    month = current_date.month
    if month in [12, 1, 2]:  # Winter - higher diabetes management
        seasonal_mult = 1.5
    elif month in [6, 7, 8]:  # Summer - moderate demand
        seasonal_mult = 0.8
    elif month in [3, 4, 5]:  # Spring - moderate
        seasonal_mult = 1.0
    else:  # Fall - moderate
        seasonal_mult = 1.2
    
    # Weekday patterns
    weekday = current_date.weekday()
    if weekday == 6:  # Sunday
        weekday_mult = 0.4
    elif weekday == 5:  # Saturday
        weekday_mult = 0.7
    elif weekday in [0, 1, 2, 3, 4]:  # Weekdays
        weekday_mult = 1.3
    else:
        weekday_mult = 1.0
    
    # Growth trend
    years_elapsed = (current_date - start_date).days / 365.25
    growth_factor = (1 + 0.15) ** years_elapsed  # 15% annual growth
    
    # Random variation
    random_factor = random.uniform(0.6, 1.4)
    
    # Calculate final sales
    daily_sales = int(base_sales * seasonal_mult * weekday_mult * growth_factor * random_factor)
    
    return max(10, daily_sales)  # Minimum 10 sales per day

def generate_metformin_simple():
    print("=== Simple Metformin Data Generator for Sales Rep 'ace' ===")
    print("Creating 25 years of data (2000-2025) for maximum forecasting accuracy")
    
    # 1. Get medicine
    try:
        metformin = Medicine.objects.get(id=4)  # Metformin 500mg
        print(f"✅ Found medicine: {metformin.name}")
    except Medicine.DoesNotExist:
        print("❌ Metformin not found in inventory.")
        return

    # 2. Get ace sales rep
    ace_sales_rep_id = get_ace_sales_rep()
    if not ace_sales_rep_id:
        print("❌ Sales rep 'ace' not available")
        return
    print(f"✅ Found sales rep 'ace' (ID: {ace_sales_rep_id})")

    # 3. Clear existing data for medicine 4
    print("\n🧹 Clearing existing data...")
    db_path = get_database_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM orders_orderitem WHERE medicine_id = 4")
        cursor.execute("DELETE FROM orders_orderstatushistory WHERE order_id IN (SELECT id FROM orders_order WHERE sales_rep_id = ?)", (ace_sales_rep_id,))
        cursor.execute("DELETE FROM orders_order WHERE sales_rep_id = ?", (ace_sales_rep_id,))
        cursor.execute("DELETE FROM inventory_stockmovement WHERE medicine_id = 4")
        conn.commit()
        print("✅ Cleared existing data")
    except Exception as e:
        print(f"⚠️  Error clearing data: {e}")
    finally:
        if conn:
            conn.close()

    # 4. Define date range (2000-2025) - 25 years
    start_date = date(2000, 1, 1)
    end_date = date(2025, 12, 31)
    
    # 5. Generate data
    current_date = start_date
    order_id = 1
    stock_movement_id = 1
    total_orders = 0
    total_items = 0
    current_stock = 10000
    
    print(f"\n📊 Generating data from {start_date} to {end_date}")
    
    # Create initial stock movement
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO inventory_stockmovement 
            (id, medicine_id, movement_type, quantity, reason, created_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            stock_movement_id,
            4,  # Metformin ID
            'in',
            current_stock,
            'Initial stock for Metformin 500mg',
            start_date.isoformat(),
            'Initial stock setup for historical data generation'
        ))
        conn.commit()
        stock_movement_id += 1
        print(f"✅ Created initial stock: {current_stock} units")
    except Exception as e:
        print(f"⚠️  Error creating initial stock: {e}")
    finally:
        if conn:
            conn.close()
    
    # Generate daily data
    while current_date <= end_date:
        daily_sales = calculate_daily_sales(current_date, start_date)
        
        if daily_sales > 0 and current_stock >= daily_sales:
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                cursor = conn.cursor()
                
                # Create order
                cursor.execute("""
                    INSERT INTO orders_order 
                    (id, customer_name, customer_email, customer_phone, total_amount, 
                     status, sales_rep_id, created_at, updated_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    f"Customer_{order_id:06d}",
                    f"customer_{order_id}@example.com",
                    f"555-{random.randint(1000, 9999)}",
                    round(float(metformin.unit_price * daily_sales), 2),
                    'delivered',
                    ace_sales_rep_id,
                    current_date.isoformat(),
                    current_date.isoformat(),
                    f'Metformin order for {current_date.strftime("%Y-%m-%d")}'
                ))
                
                # Create order item
                cursor.execute("""
                    INSERT INTO orders_orderitem 
                    (id, order_id, medicine_id, quantity, unit_price, total_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    order_id,
                    order_id,
                    4,  # Metformin ID
                    daily_sales,
                    float(metformin.unit_price),
                    round(float(metformin.unit_price * daily_sales), 2),
                    current_date.isoformat()
                ))
                
                # Create order status history
                cursor.execute("""
                    INSERT INTO orders_orderstatushistory 
                    (id, order_id, status, created_at, notes)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    order_id,
                    order_id,
                    'delivered',
                    current_date.isoformat(),
                    f'Order delivered on {current_date.strftime("%Y-%m-%d")}'
                ))
                
                # Create stock movement (out)
                cursor.execute("""
                    INSERT INTO inventory_stockmovement 
                    (id, medicine_id, movement_type, quantity, reason, created_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_movement_id,
                    4,  # Metformin ID
                    'out',
                    daily_sales,
                    f'Sale on {current_date.strftime("%Y-%m-%d")}',
                    current_date.isoformat(),
                    f'Stock movement for order {order_id}'
                ))
                
                conn.commit()
                
                # Update counters
                current_stock -= daily_sales
                total_orders += 1
                total_items += daily_sales
                order_id += 1
                stock_movement_id += 1
                
            except Exception as e:
                print(f"⚠️  Error creating order for {current_date}: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Replenish stock if low (every 30 days)
        if current_date.day == 1 and current_stock < 5000:
            replenishment = random.randint(8000, 12000)
            try:
                conn = sqlite3.connect(db_path, timeout=30.0)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO inventory_stockmovement 
                    (id, medicine_id, movement_type, quantity, reason, created_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    stock_movement_id,
                    4,  # Metformin ID
                    'in',
                    replenishment,
                    f'Monthly replenishment for {current_date.strftime("%Y-%m")}',
                    current_date.isoformat(),
                    f'Stock replenishment on {current_date.strftime("%Y-%m-%d")}'
                ))
                
                conn.commit()
                current_stock += replenishment
                stock_movement_id += 1
                print(f"📦 Replenished stock: +{replenishment} units (Total: {current_stock})")
            except Exception as e:
                print(f"⚠️  Error replenishing stock: {e}")
            finally:
                if conn:
                    conn.close()
        
        # Move to next day
        current_date += timedelta(days=1)
        
        # Progress update every 1000 days
        if (current_date - start_date).days % 1000 == 0:
            progress = ((current_date - start_date).days / (end_date - start_date).days) * 100
            print(f"📈 Progress: {progress:.1f}% - {total_orders} orders, {total_items} items")
    
    # Final summary
    print(f"\n✅ Data generation completed!")
    print(f"📊 Summary:")
    print(f"   • Date range: {start_date} to {end_date}")
    print(f"   • Total orders: {total_orders:,}")
    print(f"   • Total items sold: {total_items:,}")
    print(f"   • Total sales value: ${total_items * float(metformin.unit_price):,.2f}")
    print(f"   • Final stock: {current_stock:,} units")
    print(f"   • Data points for forecasting: {total_items:,}")
    print(f"   • Years of data: {((end_date - start_date).days / 365.25):.1f}")
    
    # Verify data
    print(f"\n🔍 Verifying data...")
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM orders_order WHERE sales_rep_id = ?", (ace_sales_rep_id,))
        order_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM orders_orderitem WHERE medicine_id = 4")
        item_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM inventory_stockmovement WHERE medicine_id = 4")
        stock_count = cursor.fetchone()[0]
        
        print(f"✅ Verification successful:")
        print(f"   • Orders in database: {order_count:,}")
        print(f"   • Order items in database: {item_count:,}")
        print(f"   • Stock movements in database: {stock_count:,}")
        
    except Exception as e:
        print(f"⚠️  Error verifying data: {e}")
    finally:
        if conn:
            conn.close()
    
    print(f"\n🎯 Ready for ARIMA forecasting with {total_items:,} data points!")
    print(f"   This should provide excellent forecasting accuracy with 25 years of data.")

if __name__ == "__main__":
    generate_metformin_simple()
