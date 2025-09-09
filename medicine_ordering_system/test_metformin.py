#!/usr/bin/env python3
"""
Test script to check Metformin data generation
"""

import os
import sys
import django
import sqlite3

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

def check_data():
    print("=== Checking Metformin Data ===")
    
    # Check database directly
    db_path = 'db.sqlite3'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check orders
        cursor.execute("SELECT COUNT(*) FROM orders_order")
        order_count = cursor.fetchone()[0]
        print(f"Total orders: {order_count}")
        
        # Check order items for Metformin (ID 4)
        cursor.execute("SELECT COUNT(*) FROM orders_orderitem WHERE medicine_id = 4")
        metformin_items = cursor.fetchone()[0]
        print(f"Metformin order items: {metformin_items}")
        
        # Check stock movements for Metformin
        cursor.execute("SELECT COUNT(*) FROM inventory_stockmovement WHERE medicine_id = 4")
        stock_movements = cursor.fetchone()[0]
        print(f"Metformin stock movements: {stock_movements}")
        
        # Check if ace user exists
        cursor.execute("SELECT id, username, role FROM accounts_user WHERE username = 'ace'")
        ace_user = cursor.fetchone()
        if ace_user:
            print(f"Ace user found: ID={ace_user[0]}, Role={ace_user[2]}")
        else:
            print("Ace user not found!")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking data: {e}")

if __name__ == "__main__":
    check_data()
