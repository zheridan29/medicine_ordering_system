#!/usr/bin/env python3
"""
Database Check Script
Checks current user data in the database
"""

import sqlite3
from datetime import datetime

def check_database():
    """Check current user data in the database"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking Current Database...")
    print("=" * 50)
    
    # Get total user count
    cursor.execute("SELECT COUNT(*) FROM accounts_user")
    total_users = cursor.fetchone()[0]
    print(f"Total users: {total_users}")
    
    # Get users by role
    cursor.execute("SELECT role, COUNT(*) FROM accounts_user GROUP BY role")
    role_counts = cursor.fetchall()
    print("\nUsers by role:")
    for role, count in role_counts:
        print(f"  {role}: {count}")
    
    # Get sample users
    cursor.execute("SELECT username, role, email, created_at FROM accounts_user ORDER BY created_at DESC LIMIT 10")
    sample_users = cursor.fetchall()
    print("\nSample users (latest 10):")
    for user in sample_users:
        username, role, email, created_at = user
        created_str = created_at[:19] if created_at else "Unknown"
        print(f"  {username} - {role} - {email} - {created_str}")
    
    # Check sales rep profiles
    cursor.execute("SELECT COUNT(*) FROM accounts_salesrepprofile")
    sales_reps = cursor.fetchone()[0]
    print(f"\nSales rep profiles: {sales_reps}")
    
    # Check pharmacist profiles
    cursor.execute("SELECT COUNT(*) FROM accounts_pharmacistadminprofile")
    pharmacists = cursor.fetchone()[0]
    print(f"Pharmacist profiles: {pharmacists}")
    
    # Check user sessions
    cursor.execute("SELECT COUNT(*) FROM accounts_usersession")
    sessions = cursor.fetchone()[0]
    print(f"User sessions: {sessions}")
    
    # Check orders
    cursor.execute("SELECT COUNT(*) FROM orders_order")
    orders = cursor.fetchone()[0]
    print(f"Orders: {orders}")
    
    # Check medicines
    cursor.execute("SELECT COUNT(*) FROM inventory_medicine")
    medicines = cursor.fetchone()[0]
    print(f"Medicines: {medicines}")
    
    conn.close()
    
    print("\n✅ Database check complete!")

if __name__ == "__main__":
    check_database()
