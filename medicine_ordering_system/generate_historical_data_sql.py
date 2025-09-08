#!/usr/bin/env python
"""
Generate historical transactional data using direct SQL insertion
This bypasses Django's timezone handling for guaranteed historical dates
Works with medicines from generate_medicines.py and respects stock limits
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

def get_medicine_data():
    """Get medicine data from the database"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all medicines with their current stock
    cursor.execute("""
        SELECT id, name, generic_name, unit_price, current_stock, prescription_type, category_id
        FROM inventory_medicine 
        WHERE is_active = 1 AND is_available = 1
        ORDER BY name
    """)
    
    medicines = cursor.fetchall()
    conn.close()
    
    return medicines

def get_available_stock(medicine_id, order_date):
    """Calculate available stock for a medicine on a specific date"""
    db_path = get_database_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)  # Add timeout
        cursor = conn.cursor()
        
        # Get initial stock from the medicine record
        cursor.execute("SELECT current_stock FROM inventory_medicine WHERE id = ?", (medicine_id,))
        result = cursor.fetchone()
        initial_stock = result[0] if result else 0
        
        # Calculate stock movements up to the order date
        cursor.execute("""
            SELECT SUM(quantity) 
            FROM inventory_stockmovement 
            WHERE medicine_id = ? AND created_at <= ?
        """, (medicine_id, order_date.isoformat()))
        
        result = cursor.fetchone()
        stock_change = result[0] if result and result[0] else 0
        available_stock = initial_stock + stock_change  # Add because movements can be positive (in) or negative (out)
        
        return max(0, available_stock)
    except sqlite3.OperationalError as e:
        print(f"Database error: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def create_historical_orders_sql(medicine_id, medicine_name, unit_price, sales_rep_id, customer_ids, start_year, end_year):
    """Create historical orders using direct SQL with stock validation"""
    
    db_path = get_database_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)  # Add timeout
        cursor = conn.cursor()
        
        print(f"Creating historical orders for {medicine_name} from {start_year} to {end_year}...")
        
        # Seasonal patterns based on medicine type
        if 'vitamin' in medicine_name.lower() or 'supplement' in medicine_name.lower():
        # Vitamins: higher in winter, flu season
        seasonal_multipliers = {
            1: 1.4, 2: 1.3, 3: 1.1, 4: 0.9, 5: 0.8, 6: 0.7, 7: 0.6, 8: 0.7, 9: 0.8, 10: 0.9, 11: 1.2, 12: 1.3
        }
    elif 'pain' in medicine_name.lower() or 'ibuprofen' in medicine_name.lower() or 'paracetamol' in medicine_name.lower():
        # Pain relief: higher in winter months
        seasonal_multipliers = {
            1: 1.2, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.8, 6: 0.7, 7: 0.7, 8: 0.8, 9: 0.9, 10: 1.0, 11: 1.1, 12: 1.2
        }
    elif 'antibiotic' in medicine_name.lower() or 'amoxicillin' in medicine_name.lower():
        # Antibiotics: higher in flu season
        seasonal_multipliers = {
            1: 1.3, 2: 1.2, 3: 1.0, 4: 0.8, 5: 0.7, 6: 0.6, 7: 0.6, 8: 0.7, 9: 0.8, 10: 0.9, 11: 1.1, 12: 1.2
        }
    elif 'diabetes' in medicine_name.lower() or 'metformin' in medicine_name.lower():
        # Diabetes medication: consistent throughout year
        seasonal_multipliers = {
            1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0
        }
    else:
        # Default: slight seasonal variation
        seasonal_multipliers = {
            1: 1.1, 2: 1.0, 3: 1.0, 4: 0.9, 5: 0.9, 6: 0.8, 7: 0.8, 8: 0.9, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.1
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
    
    # Track stock depletion
    stock_depleted = False
    stock_depletion_date = None
    
    # Growth trend over years
    base_growth = 1.0
    year_growth_rate = 0.05  # 5% annual growth
    
    while current_date <= end_date and not stock_depleted:
        year = current_date.year
        month = current_date.month
        weekday = current_date.weekday()
        
        # Calculate growth factor for this year
        years_from_start = year - start_year
        growth_factor = base_growth * (1 + year_growth_rate) ** years_from_start
        
        # Apply seasonal and weekday multipliers
        seasonal_mult = seasonal_multipliers.get(month, 1.0)
        weekday_mult = weekday_multipliers.get(weekday, 1.0)
        
        # Check available stock at the beginning of the day
        available_stock = get_available_stock(medicine_id, current_date)
        
        if available_stock <= 0:
            if not stock_depleted:
                stock_depleted = True
                stock_depletion_date = current_date
                print(f"    ⚠️  Stock depleted for {medicine_name} on {current_date}")
            current_date += timedelta(days=1)
            continue
        
        # Base daily sales (increases over time, but reduces when stock is low)
        base_orders = max(1, int(1 + years_from_start * 0.1))  # 1-3 orders per day
        
        # Reduce order frequency when stock is low
        stock_availability_factor = min(1.0, available_stock / 100)  # Reduce orders when stock < 100
        daily_orders = max(1, int(base_orders * seasonal_mult * weekday_mult * growth_factor * stock_availability_factor))
        
        # Generate orders for the day
        daily_orders_created = 0
        for _ in range(daily_orders):
            customer_id = random.choice(customer_ids)
            
            # Re-check available stock for each order (in case previous orders reduced it)
            available_stock = get_available_stock(medicine_id, current_date)
            
            if available_stock <= 0:
                break  # Stop generating orders for this day if stock is depleted
            
            # Order quantity (1-10 units, respecting stock limits)
            # Prefer smaller orders when stock is low
            if available_stock < 50:
                max_quantity = min(3, available_stock)  # Max 3 units when stock is low
            elif available_stock < 100:
                max_quantity = min(5, available_stock)  # Max 5 units when stock is medium
            else:
                max_quantity = min(10, available_stock)  # Max 10 units when stock is high
            
            quantity = random.randint(1, max_quantity)
            
            # Calculate pricing
            total_amount = unit_price * quantity
            tax_amount = total_amount * 0.08  # 8% tax
            shipping_cost = 5.99 if total_amount < 50 else 0.0  # Free shipping over $50
            discount_amount = total_amount * 0.05 if quantity >= 5 else 0.0  # 5% discount for bulk orders
            final_total = total_amount + tax_amount + shipping_cost - discount_amount
            
            # Create order with historical date
            order_number = f"ORD{current_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            # Insert order with proper historical datetime
            order_datetime = datetime.combine(current_date, datetime.min.time())
            confirmed_datetime = order_datetime + timedelta(hours=1)
            shipped_datetime = order_datetime + timedelta(hours=2)
            delivered_datetime = order_datetime + timedelta(hours=4)
            
            # Random order status based on date (older orders more likely to be completed)
            status_choices = ['delivered', 'shipped', 'confirmed', 'pending']
            status_weights = [0.7, 0.2, 0.08, 0.02] if year < 2024 else [0.3, 0.3, 0.3, 0.1]
            status = random.choices(status_choices, weights=status_weights)[0]
            
            # Payment status based on order status
            payment_status = 'paid' if status in ['delivered', 'shipped'] else random.choice(['paid', 'pending'])
            
            cursor.execute("""
                INSERT INTO orders_order (
                    order_number, sales_rep_id, customer_name, customer_phone, customer_address,
                    status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
                    delivery_method, delivery_address, delivery_instructions, prescription_required,
                    prescription_verified, customer_notes, internal_notes, created_at, updated_at,
                    confirmed_at, shipped_at, delivered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_number, sales_rep_id, f"Customer {customer_id}", "+1-555-0123", "123 Main St, City, State 12345",
                status, payment_status, str(total_amount), str(tax_amount), str(shipping_cost), str(discount_amount), str(final_total),
                'delivery', "123 Main St, City, State 12345", f"Delivery instructions for {medicine_name}",
                'prescription' in medicine_name.lower(), False, f"Customer notes for {medicine_name}", f"Internal notes for {medicine_name}",
                order_datetime.isoformat(), order_datetime.isoformat(),
                confirmed_datetime.isoformat() if status in ['confirmed', 'shipped', 'delivered'] else None,
                shipped_datetime.isoformat() if status in ['shipped', 'delivered'] else None,
                delivered_datetime.isoformat() if status == 'delivered' else None
            ))
            
            order_id = cursor.lastrowid
            
            # Insert order item
            cursor.execute("""
                INSERT INTO orders_orderitem (
                    order_id, medicine_id, quantity, unit_price, total_price, prescription_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id, medicine_id, quantity, str(unit_price), str(total_amount), 
                f"Prescription notes for {medicine_name}", order_datetime.isoformat()
            ))
            
            # Update stock movement (stock out) - get next available ID
            cursor.execute("SELECT MAX(id) FROM inventory_stockmovement")
            max_id = cursor.fetchone()[0] or 0
            next_id = max_id + 1
            
            cursor.execute("""
                INSERT INTO inventory_stockmovement (
                    id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                next_id, medicine_id, 'out', -quantity, order_number, f'Sale of {medicine_name} - Order {order_number}',
                sales_rep_id, order_datetime.isoformat()
            ))
            
            orders_created += 1
            daily_orders_created += 1
        
        # Report daily activity
        if daily_orders_created > 0:
            print(f"    📅 {current_date}: {daily_orders_created} orders, {available_stock} units remaining")
        
        current_date += timedelta(days=1)
    
        conn.commit()
        
        # Report final statistics
        if stock_depleted:
            print(f"✅ Created {orders_created} orders for {medicine_name} (Stock depleted on {stock_depletion_date})")
        else:
            print(f"✅ Created {orders_created} orders for {medicine_name} (Stock remaining: {available_stock})")
        
        return orders_created
        
    except sqlite3.OperationalError as e:
        print(f"Database error for {medicine_name}: {e}")
        return 0
    except Exception as e:
        print(f"Error creating orders for {medicine_name}: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def add_stock_replenishment_events(medicines, sales_rep_id, start_year, end_year):
    """Add realistic stock replenishment events throughout the period"""
    db_path = get_database_path()
    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        for medicine in medicines:
            medicine_id, name, generic_name, unit_price, current_stock, prescription_type, category_id = medicine
            
            # Add 2-4 replenishment events per year
            replenishment_count = random.randint(2, 4) * (end_year - start_year + 1)
            
            for _ in range(replenishment_count):
                # Random date within the period
                random_year = random.randint(start_year, end_year)
                random_month = random.randint(1, 12)
                random_day = random.randint(1, 28)  # Safe day for all months
                replenishment_date = date(random_year, random_month, random_day)
                
                # Random replenishment quantity (10-50% of current stock)
                replenishment_quantity = random.randint(int(current_stock * 0.1), int(current_stock * 0.5))
                
                # Get next available ID
                cursor.execute("SELECT MAX(id) FROM inventory_stockmovement")
                max_id = cursor.fetchone()[0] or 0
                next_id = max_id + 1
                
                # Create replenishment movement
                cursor.execute("""
                    INSERT INTO inventory_stockmovement (
                        id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    next_id,
                    medicine_id,
                    'in',
                    replenishment_quantity,
                    f'RESTOCK-{random.randint(1000, 9999)}',
                    f'Stock replenishment for {name}',
                    sales_rep_id,
                    replenishment_date.isoformat()
                ))
        
        conn.commit()
        
    except sqlite3.OperationalError as e:
        print(f"Database error in stock replenishment: {e}")
    except Exception as e:
        print(f"Error in stock replenishment: {e}")
    finally:
        if conn:
            conn.close()

def main():
    """Main function to generate historical data for all medicines"""
    print("=== HISTORICAL DATA GENERATION (SQL) ===")
    print("Using direct SQL insertion for guaranteed historical dates")
    print("Working with medicines from generate_medicines.py")
    print("Respecting stock limits to prevent overselling")
    print()
    
    # Get all medicines
    medicines = get_medicine_data()
    if not medicines:
        print("❌ No medicines found. Please run generate_medicines.py first.")
        return
    
    print(f"✅ Found {len(medicines)} medicines:")
    for med in medicines:
        print(f"  • {med[1]} ({med[2]}) - ${med[3]} - Stock: {med[4]}")
    print()
    
    # Get sales rep - try different roles
    sales_rep = None
    for role in ['sales_rep', 'pharmacist_admin', 'admin']:
        try:
            sales_rep = User.objects.filter(role=role).first()
            if sales_rep:
                print(f"✅ Found sales rep: {sales_rep.first_name} {sales_rep.last_name} (ID: {sales_rep.id}, Role: {sales_rep.role})")
                break
        except:
            continue
    
    if not sales_rep:
        # Use any user as sales rep
        sales_rep = User.objects.first()
        if sales_rep:
            print(f"✅ Using user as sales rep: {sales_rep.first_name} {sales_rep.last_name} (ID: {sales_rep.id}, Role: {sales_rep.role})")
        else:
            print("❌ No users found. Please create users first.")
            return
    
    # Get customer IDs - use all users as potential customers
    all_users = User.objects.all()
    customer_ids = [u.id for u in all_users]
    if not customer_ids:
        print("❌ No users found. Please create users first.")
        return
    
    print(f"✅ Found {len(customer_ids)} customers")
    print()
    
    # Clear existing order data
    print("Clearing existing order data...")
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM orders_orderitem")
        cursor.execute("DELETE FROM orders_order")
        cursor.execute("DELETE FROM inventory_stockmovement WHERE movement_type = 'out'")
    print("✅ Data cleared")
    print()
    
    # Generate historical data for each medicine
    start_year = 2020
    end_year = 2024
    
    total_orders = 0
    medicine_stats = []
    
    # Add some stock replenishment events to make data more realistic
    print("Adding stock replenishment events...")
    add_stock_replenishment_events(medicines, sales_rep.id, start_year, end_year)
    print("✅ Stock replenishment events added")
    print()
    
    for medicine in medicines:
        medicine_id, name, generic_name, unit_price, current_stock, prescription_type, category_id = medicine
        
        print(f"Generating data for {name}...")
        
        orders_created = create_historical_orders_sql(
            medicine_id, 
            name, 
            float(unit_price), 
            sales_rep.id, 
            customer_ids, 
            start_year, 
            end_year
        )
        
        total_orders += orders_created
        medicine_stats.append((name, orders_created))
        print()
    
    print("=== VERIFICATION ===")
    
    # Verify the data for each medicine
    for medicine in medicines:
        medicine_id, name, generic_name, unit_price, current_stock, prescription_type, category_id = medicine
        
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
            """, [medicine_id])
            
            result = cursor.fetchone()
            if result and result[0] > 0:
                order_count, first_order, last_order, total_quantity, total_revenue = result
                print(f"✅ {name}:")
                print(f"   Orders: {order_count:,} | Quantity: {total_quantity:,} | Revenue: ${total_revenue:,.2f}")
                print(f"   Date Range: {first_order[:10]} to {last_order[:10]}")
            else:
                print(f"❌ {name}: No orders created")
    
    print()
    print("=== SUMMARY ===")
    print(f"✅ Total Orders Created: {total_orders:,}")
    print(f"✅ Date Range: {start_year} to {end_year}")
    print(f"✅ Medicines Processed: {len(medicines)}")
    print()
    print("=== HISTORICAL DATA GENERATION COMPLETE ===")
    print("✅ All dates are properly historical (2020-2024)")
    print("✅ No timezone conversion issues")
    print("✅ Stock limits respected - no overselling")
    print("✅ Ready for forecasting and analytics")

if __name__ == "__main__":
    main()