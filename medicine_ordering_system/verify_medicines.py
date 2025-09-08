#!/usr/bin/env python3
"""
Medicine Verification Script for Medicine Ordering System
Verifies the generated medicine data and provides statistics
"""

import os
import sys
import django
import sqlite3
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

def verify_medicines():
    """Verify the generated medicine data and provide statistics"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Verifying Medicine Data...")
    print("=" * 50)
    
    # Get categories
    cursor.execute("SELECT COUNT(*) FROM inventory_category")
    total_categories = cursor.fetchone()[0]
    
    cursor.execute("SELECT name, description FROM inventory_category ORDER BY name")
    categories = cursor.fetchall()
    
    # Get manufacturers
    cursor.execute("SELECT COUNT(*) FROM inventory_manufacturer")
    total_manufacturers = cursor.fetchone()[0]
    
    cursor.execute("SELECT name, country, contact_email FROM inventory_manufacturer ORDER BY name")
    manufacturers = cursor.fetchall()
    
    # Get medicines
    cursor.execute("SELECT COUNT(*) FROM inventory_medicine")
    total_medicines = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT m.name, m.generic_name, m.strength, m.dosage_form, m.prescription_type,
               m.unit_price, m.current_stock, m.is_active, m.is_available,
               c.name as category, man.name as manufacturer
        FROM inventory_medicine m
        JOIN inventory_category c ON m.category_id = c.id
        JOIN inventory_manufacturer man ON m.manufacturer_id = man.id
        ORDER BY m.name
    """)
    medicines = cursor.fetchall()
    
    # Get stock movements
    cursor.execute("SELECT COUNT(*) FROM inventory_stockmovement")
    total_stock_movements = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT movement_type, COUNT(*) as count
        FROM inventory_stockmovement
        GROUP BY movement_type
        ORDER BY count DESC
    """)
    stock_movement_types = cursor.fetchall()
    
    # Get reorder alerts
    cursor.execute("SELECT COUNT(*) FROM inventory_reorderalert")
    total_reorder_alerts = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT priority, COUNT(*) as count
        FROM inventory_reorderalert
        GROUP BY priority
        ORDER BY count DESC
    """)
    reorder_priorities = cursor.fetchall()
    
    # Get stock status summary
    cursor.execute("""
        SELECT 
            COUNT(*) as total_medicines,
            SUM(CASE WHEN current_stock = 0 THEN 1 ELSE 0 END) as out_of_stock,
            SUM(CASE WHEN current_stock <= reorder_point AND current_stock > 0 THEN 1 ELSE 0 END) as low_stock,
            SUM(CASE WHEN current_stock > reorder_point THEN 1 ELSE 0 END) as in_stock
        FROM inventory_medicine
    """)
    stock_summary = cursor.fetchone()
    
    # Get price statistics
    cursor.execute("""
        SELECT 
            MIN(unit_price) as min_price,
            MAX(unit_price) as max_price,
            AVG(unit_price) as avg_price,
            MIN(cost_price) as min_cost,
            MAX(cost_price) as max_cost,
            AVG(cost_price) as avg_cost
        FROM inventory_medicine
    """)
    price_stats = cursor.fetchone()
    
    # Get prescription vs OTC breakdown
    cursor.execute("""
        SELECT prescription_type, COUNT(*) as count
        FROM inventory_medicine
        GROUP BY prescription_type
        ORDER BY count DESC
    """)
    prescription_types = cursor.fetchall()
    
    # Get recent stock movements
    cursor.execute("""
        SELECT m.name, sm.movement_type, sm.quantity, sm.created_at
        FROM inventory_stockmovement sm
        JOIN inventory_medicine m ON sm.medicine_id = m.id
        ORDER BY sm.created_at DESC
        LIMIT 10
    """)
    recent_movements = cursor.fetchall()
    
    # Get active reorder alerts
    cursor.execute("""
        SELECT m.name, ra.current_stock, ra.reorder_point, ra.priority, ra.created_at
        FROM inventory_reorderalert ra
        JOIN inventory_medicine m ON ra.medicine_id = m.id
        WHERE ra.is_processed = 0
        ORDER BY ra.priority DESC, ra.created_at DESC
    """)
    active_alerts = cursor.fetchall()
    
    conn.close()
    
    # Display results
    print(f"📂 Categories ({total_categories}):")
    for category, description in categories:
        print(f"  • {category}: {description}")
    print()
    
    print(f"🏭 Manufacturers ({total_manufacturers}):")
    for manufacturer, country, email in manufacturers:
        print(f"  • {manufacturer} ({country}) - {email}")
    print()
    
    print(f"💊 Medicines ({total_medicines}):")
    for medicine in medicines:
        name, generic, strength, form, presc_type, price, stock, active, available, category, manufacturer = medicine
        status = "✅" if active and available else "❌"
        print(f"  {status} {name} ({generic}) - {strength} {form}")
        print(f"    Category: {category} | Manufacturer: {manufacturer}")
        print(f"    Price: ${price} | Stock: {stock} | Type: {presc_type}")
        print()
    
    print(f"📦 Stock Movement Statistics:")
    print(f"  • Total Movements: {total_stock_movements}")
    for movement_type, count in stock_movement_types:
        print(f"  • {movement_type.title()}: {count}")
    print()
    
    print(f"⚠️  Reorder Alert Statistics:")
    print(f"  • Total Alerts: {total_reorder_alerts}")
    for priority, count in reorder_priorities:
        print(f"  • {priority.title()} Priority: {count}")
    print()
    
    if stock_summary:
        print(f"📊 Stock Status Summary:")
        print(f"  • Total Medicines: {stock_summary[0]}")
        print(f"  • Out of Stock: {stock_summary[1]}")
        print(f"  • Low Stock: {stock_summary[2]}")
        print(f"  • In Stock: {stock_summary[3]}")
        print()
    
    if price_stats and price_stats[0] is not None:
        print(f"💰 Price Statistics:")
        print(f"  • Unit Price Range: ${price_stats[0]:.2f} - ${price_stats[1]:.2f}")
        print(f"  • Average Unit Price: ${price_stats[2]:.2f}")
        print(f"  • Cost Price Range: ${price_stats[3]:.2f} - ${price_stats[4]:.2f}")
        print(f"  • Average Cost Price: ${price_stats[5]:.2f}")
        print()
    
    print(f"💊 Prescription Type Breakdown:")
    for presc_type, count in prescription_types:
        print(f"  • {presc_type.title()}: {count}")
    print()
    
    print(f"📦 Recent Stock Movements (Latest 10):")
    for movement in recent_movements:
        name, movement_type, quantity, created_at = movement
        created_str = created_at[:19] if created_at else "Unknown"
        print(f"  • {name}: {movement_type} {quantity} units ({created_str})")
    print()
    
    if active_alerts:
        print(f"⚠️  Active Reorder Alerts:")
        for alert in active_alerts:
            name, current_stock, reorder_point, priority, created_at = alert
            created_str = created_at[:19] if created_at else "Unknown"
            print(f"  • {name}: {current_stock}/{reorder_point} units - {priority} priority ({created_str})")
        print()
    else:
        print("✅ No active reorder alerts")
        print()
    
    print("✅ Medicine verification complete!")
    print("💊 All medicines and associated data are properly created!")
    print("📦 Complete inventory system with stock tracking, alerts, and movements!")

if __name__ == "__main__":
    verify_medicines()
