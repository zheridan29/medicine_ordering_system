#!/usr/bin/env python3
"""
Script to check Metformin records in the database
"""

import os
import sys
import django
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from inventory.models import Medicine
from orders.models import Order, OrderItem

def check_metformin_records():
    """Check all Metformin-related records in the database"""
    
    print("🔍 Checking Metformin Records in Database")
    print("=" * 50)
    
    # Find Metformin medicine
    try:
        metformin = Medicine.objects.get(name__icontains='Metformin')
        print(f"✅ Found Metformin: {metformin.name} (ID: {metformin.id})")
        print(f"   Generic Name: {metformin.generic_name}")
        print(f"   Current Stock: {metformin.current_stock}")
        print(f"   Unit Price: ${metformin.unit_price}")
        print()
    except Medicine.DoesNotExist:
        print("❌ Metformin not found in database")
        return
    except Medicine.MultipleObjectsReturned:
        metformin_list = Medicine.objects.filter(name__icontains='Metformin')
        print(f"⚠️  Multiple Metformin records found ({metformin_list.count()}):")
        for med in metformin_list:
            print(f"   - {med.name} (ID: {med.id})")
        metformin = metformin_list.first()
        print(f"   Using first one: {metformin.name}")
        print()
    
    # Count orders containing Metformin
    metformin_orders = Order.objects.filter(items__medicine=metformin).distinct()
    total_orders = metformin_orders.count()
    
    print(f"📊 Order Statistics for {metformin.name}:")
    print(f"   Total Orders containing Metformin: {total_orders}")
    
    if total_orders > 0:
        # Count order items (individual Metformin purchases)
        metformin_items = OrderItem.objects.filter(medicine=metformin)
        total_items = metformin_items.count()
        total_quantity = sum(item.quantity for item in metformin_items)
        total_revenue = sum(item.total_price for item in metformin_items)
        
        print(f"   Total Metformin Items Sold: {total_items}")
        print(f"   Total Quantity Sold: {total_quantity} units")
        print(f"   Total Revenue: ${total_revenue:.2f}")
        
        # Status breakdown
        print(f"\n📈 Order Status Breakdown:")
        status_counts = {}
        for order in metformin_orders:
            status = order.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            print(f"   {status.title()}: {count} orders")
        
        # Recent orders
        print(f"\n🕒 Recent Orders (Last 5):")
        recent_orders = metformin_orders.order_by('-created_at')[:5]
        for order in recent_orders:
            metformin_item = order.items.filter(medicine=metformin).first()
            print(f"   Order {order.order_number} - {order.customer_name} - "
                  f"Qty: {metformin_item.quantity if metformin_item else 'N/A'} - "
                  f"Status: {order.status} - {order.created_at.strftime('%Y-%m-%d %H:%M')}")
    
    else:
        print("   No orders found containing Metformin")
    
    # Check if there are any sales data for analytics
    print(f"\n📈 Analytics Data Check:")
    
    # Check for sales data in analytics
    try:
        from analytics.models import SalesData
        metformin_sales = SalesData.objects.filter(medicine=metformin)
        sales_count = metformin_sales.count()
        print(f"   Sales Data Records: {sales_count}")
        
        if sales_count > 0:
            print(f"   Date Range: {metformin_sales.first().date} to {metformin_sales.last().date}")
            total_sales = sum(sale.quantity for sale in metformin_sales)
            print(f"   Total Sales Quantity: {total_sales}")
    except ImportError:
        print("   SalesData model not found")
    except Exception as e:
        print(f"   Error checking sales data: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Analysis Complete!")

if __name__ == "__main__":
    check_metformin_records()
