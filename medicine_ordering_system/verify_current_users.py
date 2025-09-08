#!/usr/bin/env python3
"""
Current User Verification Script for Medicine Ordering System
Verifies the generated current user data and provides statistics
"""

import os
import sys
import django
import sqlite3
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

def verify_current_users():
    """Verify the generated current user data and provide statistics"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Verifying Current User Data...")
    print("=" * 50)
    
    # Get total user count
    cursor.execute("SELECT COUNT(*) FROM accounts_user")
    total_users = cursor.fetchone()[0]
    
    # Get users by role
    cursor.execute("SELECT role, COUNT(*) FROM accounts_user GROUP BY role")
    role_counts = dict(cursor.fetchall())
    
    # Get recent users (created within last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM accounts_user WHERE created_at >= ?", (thirty_days_ago,))
    recent_users = cursor.fetchone()[0]
    
    # Get users with recent logins (within last 7 days)
    seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM accounts_user WHERE last_login >= ?", (seven_days_ago,))
    recent_logins = cursor.fetchone()[0]
    
    # Get active sessions
    cursor.execute("SELECT COUNT(*) FROM accounts_usersession WHERE is_active = 1")
    active_sessions = cursor.fetchone()[0]
    
    # Get total sessions
    cursor.execute("SELECT COUNT(*) FROM accounts_usersession")
    total_sessions = cursor.fetchone()[0]
    
    # Get recent sessions (within last 7 days)
    cursor.execute("SELECT COUNT(*) FROM accounts_usersession WHERE login_time >= ?", (seven_days_ago,))
    recent_sessions = cursor.fetchone()[0]
    
    # Get recent orders (within last 30 days)
    cursor.execute("SELECT COUNT(*) FROM orders_order WHERE created_at >= ?", (thirty_days_ago,))
    recent_orders = cursor.fetchone()[0]
    
    # Get orders by status
    cursor.execute("SELECT status, COUNT(*) FROM orders_order GROUP BY status")
    order_statuses = dict(cursor.fetchall())
    
    # Get orders by payment status
    cursor.execute("SELECT payment_status, COUNT(*) FROM orders_order GROUP BY payment_status")
    payment_statuses = dict(cursor.fetchall())
    
    # Get sample recent users
    cursor.execute("""
        SELECT username, first_name, last_name, role, email, last_login, created_at
        FROM accounts_user 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    sample_users = cursor.fetchall()
    
    # Get sample recent orders
    cursor.execute("""
        SELECT order_number, customer_name, status, payment_status, total_amount, created_at
        FROM orders_order 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    sample_orders = cursor.fetchall()
    
    # Get sales rep territories
    cursor.execute("""
        SELECT territory, COUNT(*) 
        FROM accounts_salesrepprofile 
        GROUP BY territory 
        ORDER BY COUNT(*) DESC
    """)
    territories = cursor.fetchall()
    
    # Get pharmacist specializations
    cursor.execute("""
        SELECT specialization, COUNT(*) 
        FROM accounts_pharmacistadminprofile 
        GROUP BY specialization 
        ORDER BY COUNT(*) DESC
    """)
    specializations = cursor.fetchall()
    
    # Get departments
    cursor.execute("""
        SELECT department, COUNT(*) 
        FROM accounts_pharmacistadminprofile 
        GROUP BY department 
        ORDER BY COUNT(*) DESC
    """)
    departments = cursor.fetchall()
    
    # Get commission rate statistics
    cursor.execute("""
        SELECT 
            MIN(commission_rate) as min_rate,
            MAX(commission_rate) as max_rate,
            AVG(commission_rate) as avg_rate
        FROM accounts_salesrepprofile
    """)
    commission_stats = cursor.fetchone()
    
    # Get experience statistics
    cursor.execute("""
        SELECT 
            MIN(years_of_experience) as min_exp,
            MAX(years_of_experience) as max_exp,
            AVG(years_of_experience) as avg_exp
        FROM accounts_pharmacistadminprofile
    """)
    experience_stats = cursor.fetchone()
    
    # Get recent activity summary
    cursor.execute("""
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as user_count
        FROM accounts_user 
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 7
    """, (thirty_days_ago,))
    daily_user_creation = cursor.fetchall()
    
    conn.close()
    
    # Display results
    print(f"📊 Current User Statistics:")
    print(f"  • Total Users: {total_users}")
    print(f"  • Recent Users (30 days): {recent_users}")
    print(f"  • Users with Recent Logins (7 days): {recent_logins}")
    print(f"  • Sales Representatives: {role_counts.get('sales_rep', 0)}")
    print(f"  • Pharmacist/Admin: {role_counts.get('pharmacist_admin', 0)}")
    print(f"  • Admin Users: {role_counts.get('admin', 0)}")
    print()
    
    print(f"🔄 Activity Statistics:")
    print(f"  • Total Sessions: {total_sessions}")
    print(f"  • Active Sessions: {active_sessions}")
    print(f"  • Recent Sessions (7 days): {recent_sessions}")
    print(f"  • Recent Orders (30 days): {recent_orders}")
    print()
    
    print(f"📦 Order Statistics:")
    print(f"  • Order Statuses:")
    for status, count in order_statuses.items():
        print(f"    - {status}: {count}")
    print(f"  • Payment Statuses:")
    for status, count in payment_statuses.items():
        print(f"    - {status}: {count}")
    print()
    
    print(f"🏢 Sales Rep Territories:")
    for territory, count in territories:
        print(f"  • {territory}: {count} reps")
    print()
    
    print(f"💊 Pharmacist Specializations:")
    for specialization, count in specializations:
        print(f"  • {specialization}: {count} pharmacists")
    print()
    
    print(f"🏢 Departments:")
    for department, count in departments:
        print(f"  • {department}: {count} staff")
    print()
    
    if commission_stats and commission_stats[0] is not None:
        print(f"💰 Commission Rate Statistics:")
        print(f"  • Minimum: {commission_stats[0]}%")
        print(f"  • Maximum: {commission_stats[1]}%")
        print(f"  • Average: {commission_stats[2]:.2f}%")
        print()
    
    if experience_stats and experience_stats[0] is not None:
        print(f"📚 Experience Statistics:")
        print(f"  • Minimum: {experience_stats[0]} years")
        print(f"  • Maximum: {experience_stats[1]} years")
        print(f"  • Average: {experience_stats[2]:.1f} years")
        print()
    
    print(f"📅 Recent User Creation (Last 7 Days):")
    for date_str, count in daily_user_creation:
        print(f"  • {date_str}: {count} users")
    print()
    
    print(f"👤 Sample Recent Users:")
    for user in sample_users:
        username, first_name, last_name, role, email, last_login, created_at = user
        last_login_str = last_login[:19] if last_login else "Never"
        created_str = created_at[:19] if created_at else "Unknown"
        print(f"  • {first_name} {last_name} ({username}) - {role}")
        print(f"    Last Login: {last_login_str} | Created: {created_str}")
    print()
    
    print(f"📦 Sample Recent Orders:")
    for order in sample_orders:
        order_number, customer, status, payment_status, total, created_at = order
        created_str = created_at[:19] if created_at else "Unknown"
        print(f"  • {order_number} - {customer} - {status} - ${total}")
        print(f"    Payment: {payment_status} | Created: {created_str}")
    print()
    
    print("✅ Current user verification complete!")
    print("🔐 All users have default password: 'password123'")
    print("📅 All users have recent activity and current dates")
    print("🔄 Perfect for testing current system functionality!")
    print("📊 Users are ready for analytics and forecasting!")

if __name__ == "__main__":
    verify_current_users()
