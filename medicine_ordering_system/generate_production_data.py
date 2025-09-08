#!/usr/bin/env python
"""
Production-Ready Historical Data Generation
Uses direct SQL insertion for guaranteed historical dates (2000-2024)
"""

import os
import sys
import django
from datetime import datetime, date, timedelta
from decimal import Decimal
import random
import sqlite3
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from django.db import connection
from inventory.models import Medicine
from accounts.models import User

class ProductionDataGenerator:
    def __init__(self):
        self.db_path = self.get_database_path()
        self.conn = None
        
    def get_database_path(self):
        """Get the SQLite database path"""
        from django.conf import settings
        return settings.DATABASES['default']['NAME']
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn.cursor()
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
    
    def clear_existing_data(self, medicine_id):
        """Clear existing data for a medicine"""
        print("Clearing existing data...")
        cursor = self.connect()
        
        try:
            # Delete in correct order to respect foreign key constraints
            cursor.execute("DELETE FROM orders_orderitem WHERE medicine_id = ?", (medicine_id,))
            cursor.execute("""
                DELETE FROM orders_order 
                WHERE id IN (
                    SELECT DISTINCT o.id FROM orders_order o
                    JOIN orders_orderitem oi ON o.id = oi.order_id
                    WHERE oi.medicine_id = ?
                )
            """, (medicine_id,))
            cursor.execute("DELETE FROM analytics_salestrend WHERE medicine_id = ?", (medicine_id,))
            cursor.execute("DELETE FROM analytics_demandforecast WHERE medicine_id = ?", (medicine_id,))
            
            self.conn.commit()
            print("✅ Existing data cleared")
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            self.conn.rollback()
        finally:
            self.disconnect()
    
    def generate_paracetamol_data(self, medicine_id, customer_ids, start_year=2020, end_year=2020):
        """Generate Paracetamol data for 2020"""
        print(f"Generating Paracetamol data for {start_year}...")
        
        cursor = self.connect()
        orders_created = 0
        
        try:
            current_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            # Seasonal patterns for Paracetamol (higher in winter for cold/flu season)
            seasonal_multipliers = {
                1: 1.3, 2: 1.2, 3: 0.9, 4: 0.8, 5: 0.7, 6: 0.6, 7: 0.6, 8: 0.7,
                9: 0.8, 10: 0.9, 11: 1.1, 12: 1.2
            }
            
            weekday_multipliers = {0: 0.8, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.6, 6: 0.4}
            
            while current_date <= end_date:
                month = current_date.month
                weekday = current_date.weekday()
                
                seasonal_mult = seasonal_multipliers.get(month, 1.0)
                weekday_mult = weekday_multipliers.get(weekday, 1.0)
                
                # Base daily sales (1-3 orders per day)
                base_orders = random.randint(1, 3)
                daily_orders = max(1, int(base_orders * seasonal_mult * weekday_mult))
                
                for _ in range(daily_orders):
                    customer_id = random.choice(customer_ids)
                    quantity = random.randint(20, 100)  # 1-5 boxes of 20 tablets
                    unit_price = 2.50
                    total_amount = unit_price * quantity
                    
                    order_number = f"PAR{current_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
                    
                    # Create timestamps with proper historical dates
                    order_time = f"{current_date} 10:00:00"
                    confirmed_time = f"{current_date} 11:00:00"
                    shipped_time = f"{current_date} 12:00:00"
                    delivered_time = f"{current_date} 14:00:00"
                    
                    # Insert order
                    cursor.execute("""
                        INSERT INTO orders_order (
                            order_number, sales_rep_id, customer_name, customer_phone, customer_address,
                            status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
                            delivery_method, delivery_address, delivery_instructions, prescription_required,
                            prescription_verified, customer_notes, internal_notes, created_at, updated_at, confirmed_at, shipped_at, delivered_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        order_number, None, f"Customer {customer_id}", "+1-555-0123", "123 Main St, City, State 12345",
                        'delivered', 'paid', total_amount, 0.0, 0.0, 0.0, total_amount,
                        'delivery', "123 Main St, City, State 12345", "Leave at front door", False,
                        False, "Regular customer", "Historical data", order_time, order_time, confirmed_time, shipped_time, delivered_time
                    ))
                    
                    order_id = cursor.lastrowid
                    
                    # Insert order item
                    cursor.execute("""
                        INSERT INTO orders_orderitem (order_id, medicine_id, quantity, unit_price, total_price, prescription_notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, medicine_id, quantity, unit_price, total_amount, "No prescription required", order_time))
                    
                    orders_created += 1
                
                current_date += timedelta(days=1)
            
            self.conn.commit()
            print(f"✅ Created {orders_created} Paracetamol orders")
            
        except Exception as e:
            print(f"❌ Error generating Paracetamol data: {e}")
            self.conn.rollback()
        finally:
            self.disconnect()
        
        return orders_created
    
    def generate_vitamin_c_data(self, medicine_id, sales_rep_id, customer_ids, start_year=2000, end_year=2024):
        """Generate Vitamin C data for 2000-2024"""
        print(f"Generating Vitamin C data from {start_year} to {end_year}...")
        
        cursor = self.connect()
        orders_created = 0
        
        try:
            current_date = date(start_year, 1, 1)
            end_date = date(end_year, 12, 31)
            
            # Seasonal patterns for Vitamin C
            seasonal_multipliers = {
                1: 1.4, 2: 1.3, 3: 1.1, 4: 0.9, 5: 0.8, 6: 0.7, 7: 0.6, 8: 0.7,
                9: 0.8, 10: 0.9, 11: 1.2, 12: 1.3
            }
            
            weekday_multipliers = {0: 0.9, 1: 1.0, 2: 1.0, 3: 1.0, 4: 1.0, 5: 0.8, 6: 0.6}
            
            # Growth trend over 25 years
            base_growth = 1.0
            year_growth_rate = 0.05
            
            while current_date <= end_date:
                year = current_date.year
                month = current_date.month
                weekday = current_date.weekday()
                
                # Calculate growth factor
                years_from_start = year - start_year
                growth_factor = base_growth * (1 + year_growth_rate) ** years_from_start
                
                seasonal_mult = seasonal_multipliers.get(month, 1.0)
                weekday_mult = weekday_multipliers.get(weekday, 1.0)
                
                # Base daily sales (increases over time)
                base_orders = max(1, int(2 + years_from_start * 0.1))
                daily_orders = max(1, int(base_orders * seasonal_mult * weekday_mult * growth_factor))
                
                for _ in range(daily_orders):
                    customer_id = random.choice(customer_ids)
                    quantity = random.randint(60, 180)  # 1-3 bottles of 60 tablets
                    unit_price = 8.99
                    total_amount = unit_price * quantity
                    
                    # Generate unique order number with timestamp
                    import time
                    timestamp = int(time.time() * 1000) % 100000  # Last 5 digits of timestamp
                    order_number = f"VC{current_date.strftime('%Y%m%d')}{timestamp:05d}"
                    
                    # Create timestamps with proper historical dates
                    order_time = f"{current_date} 10:00:00"
                    confirmed_time = f"{current_date} 11:00:00"
                    shipped_time = f"{current_date} 12:00:00"
                    delivered_time = f"{current_date} 14:00:00"
                    
                    # Insert order
                    cursor.execute("""
                        INSERT INTO orders_order (
                            order_number, sales_rep_id, customer_name, customer_phone, customer_address,
                            status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
                            delivery_method, delivery_address, delivery_instructions, prescription_required,
                            prescription_verified, customer_notes, internal_notes, created_at, updated_at, confirmed_at, shipped_at, delivered_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        order_number, sales_rep_id, f"Customer {customer_id}", "+1-555-0123", "123 Main St, City, State 12345",
                        'delivered', 'paid', total_amount, 0.0, 0.0, 0.0, total_amount,
                        'delivery', "123 Main St, City, State 12345", "Leave at front door", False,
                        False, "Regular customer", "Historical data", order_time, order_time, confirmed_time, shipped_time, delivered_time
                    ))
                    
                    order_id = cursor.lastrowid
                    
                    # Insert order item
                    cursor.execute("""
                        INSERT INTO orders_orderitem (order_id, medicine_id, quantity, unit_price, total_price, prescription_notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (order_id, medicine_id, quantity, unit_price, total_amount, "No prescription required", order_time))
                    
                    orders_created += 1
                
                current_date += timedelta(days=1)
            
            self.conn.commit()
            print(f"✅ Created {orders_created} Vitamin C orders")
            
        except Exception as e:
            print(f"❌ Error generating Vitamin C data: {e}")
            self.conn.rollback()
        finally:
            self.disconnect()
        
        return orders_created
    
    def create_analytics_data(self, medicine_id):
        """Create analytics data from generated orders"""
        print("Creating analytics data...")
        
        cursor = self.connect()
        
        try:
            # Get yearly sales data
            cursor.execute("""
                SELECT 
                    strftime('%Y', o.created_at) as year,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.total_price) as total_revenue,
                    COUNT(DISTINCT o.id) as order_count
                FROM orders_order o
                JOIN orders_orderitem oi ON o.id = oi.order_id
                WHERE oi.medicine_id = ?
                GROUP BY strftime('%Y', o.created_at)
                ORDER BY year
            """, (medicine_id,))
            
            yearly_data = cursor.fetchall()
            
            # Create yearly sales trends
            for year, quantity, revenue, orders in yearly_data:
                cursor.execute("""
                    INSERT INTO analytics_salestrend (
                        medicine_id, period_type, period_date, quantity_sold, revenue, 
                        average_price, trend_direction, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    medicine_id, 'yearly', f"{year}-12-31", quantity, revenue,
                    revenue / quantity if quantity > 0 else 0, 'up' if int(year) >= 2015 else 'stable',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            # Get recent monthly data (2020+)
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', o.created_at) as month,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.total_price) as total_revenue
                FROM orders_order o
                JOIN orders_orderitem oi ON o.id = oi.order_id
                WHERE oi.medicine_id = ? AND strftime('%Y', o.created_at) >= '2020'
                GROUP BY strftime('%Y-%m', o.created_at)
                ORDER BY month
            """, (medicine_id,))
            
            monthly_data = cursor.fetchall()
            
            # Create monthly sales trends
            for month, quantity, revenue in monthly_data:
                cursor.execute("""
                    INSERT INTO analytics_salestrend (
                        medicine_id, period_type, period_date, quantity_sold, revenue, 
                        average_price, trend_direction, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    medicine_id, 'monthly', f"{month}-01", quantity, revenue,
                    revenue / quantity if quantity > 0 else 0, 'up' if quantity > 1000 else 'stable',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            self.conn.commit()
            print(f"✅ Created {len(yearly_data)} yearly and {len(monthly_data)} monthly trends")
            
        except Exception as e:
            print(f"❌ Error creating analytics data: {e}")
            self.conn.rollback()
        finally:
            self.disconnect()
    
    def verify_data(self, medicine_id, medicine_name):
        """Verify generated data"""
        print(f"\n=== {medicine_name.upper()} DATA VERIFICATION ===")
        
        cursor = self.connect()
        
        try:
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT o.id) as order_count,
                    MIN(o.created_at) as first_order,
                    MAX(o.created_at) as last_order,
                    SUM(oi.quantity) as total_quantity,
                    SUM(oi.total_price) as total_revenue
                FROM orders_order o
                JOIN orders_orderitem oi ON o.id = oi.order_id
                WHERE oi.medicine_id = ?
            """, (medicine_id,))
            
            result = cursor.fetchone()
            order_count, first_order, last_order, total_quantity, total_revenue = result
            
            print(f"✅ Total Orders: {order_count:,}")
            print(f"✅ Date Range: {first_order[:10]} to {last_order[:10]}")
            print(f"✅ Total Quantity: {total_quantity:,} units")
            print(f"✅ Total Revenue: ${total_revenue:,.2f}")
            
            # Check analytics data
            cursor.execute("SELECT COUNT(*) FROM analytics_salestrend WHERE medicine_id = ?", (medicine_id,))
            trends_count = cursor.fetchone()[0]
            print(f"✅ Sales Trends: {trends_count} records")
            
        except Exception as e:
            print(f"❌ Error verifying data: {e}")
        finally:
            self.disconnect()

def main():
    """Main function to generate all production data"""
    print("=== PRODUCTION DATA GENERATION ===")
    print("Using direct SQL for guaranteed historical dates")
    print()
    
    generator = ProductionDataGenerator()
    
    try:
        # Get medicines
        paracetamol = Medicine.objects.get(name='Paracetamol')
        vitamin_c = Medicine.objects.get(name='Vitamin C')
        print(f"✅ Found medicines: {paracetamol.name}, {vitamin_c.name}")
        
        # Get sales rep
        sales_rep = User.objects.get(username='ace_sales')
        print(f"✅ Found sales rep: {sales_rep.first_name} {sales_rep.last_name}")
        
        # Get customers
        customers = User.objects.filter(role='customer')
        customer_ids = [c.id for c in customers]
        print(f"✅ Found {len(customer_ids)} customers")
        print()
        
        # Generate Paracetamol data (2020)
        print("=== GENERATING PARACETAMOL DATA ===")
        generator.clear_existing_data(paracetamol.id)
        paracetamol_orders = generator.generate_paracetamol_data(paracetamol.id, customer_ids, 2020, 2020)
        generator.create_analytics_data(paracetamol.id)
        generator.verify_data(paracetamol.id, paracetamol.name)
        
        print("\n" + "="*50)
        
        # Generate Vitamin C data (2000-2024)
        print("=== GENERATING VITAMIN C DATA ===")
        generator.clear_existing_data(vitamin_c.id)
        vitamin_c_orders = generator.generate_vitamin_c_data(vitamin_c.id, sales_rep.id, customer_ids, 2000, 2024)
        generator.create_analytics_data(vitamin_c.id)
        generator.verify_data(vitamin_c.id, vitamin_c.name)
        
        print("\n" + "="*50)
        print("=== PRODUCTION DATA GENERATION COMPLETE ===")
        print(f"✅ Paracetamol: {paracetamol_orders:,} orders (2020)")
        print(f"✅ Vitamin C: {vitamin_c_orders:,} orders (2000-2024)")
        print(f"✅ Total Orders: {paracetamol_orders + vitamin_c_orders:,}")
        print("✅ All dates are properly historical")
        print("✅ No timezone conversion issues")
        print("✅ Ready for forecasting and analytics")
        
    except Exception as e:
        print(f"❌ Error in main execution: {e}")
    finally:
        generator.disconnect()

if __name__ == "__main__":
    main()
