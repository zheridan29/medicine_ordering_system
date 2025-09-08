#!/usr/bin/env python3
"""
User Verification Script for Medicine Ordering System
Verifies the generated user data and provides statistics
"""

import os
import sys
import django
import sqlite3
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

def verify_users():
    """Verify the generated user data and provide statistics"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Verifying User Data...")
    print("=" * 50)
    
    # Get total user count
    cursor.execute("SELECT COUNT(*) FROM accounts_user")
    total_users = cursor.fetchone()[0]
    
    # Get users by role
    cursor.execute("SELECT role, COUNT(*) FROM accounts_user GROUP BY role")
    role_counts = dict(cursor.fetchall())
    
    # Get sales rep profiles
    cursor.execute("SELECT COUNT(*) FROM accounts_salesrepprofile")
    sales_rep_profiles = cursor.fetchone()[0]
    
    # Get pharmacist admin profiles
    cursor.execute("SELECT COUNT(*) FROM accounts_pharmacistadminprofile")
    pharmacist_profiles = cursor.fetchone()[0]
    
    # Get user sessions
    cursor.execute("SELECT COUNT(*) FROM accounts_usersession")
    total_sessions = cursor.fetchone()[0]
    
    # Get active sessions
    cursor.execute("SELECT COUNT(*) FROM accounts_usersession WHERE is_active = 1")
    active_sessions = cursor.fetchone()[0]
    
    # Get users by verification status
    cursor.execute("SELECT is_verified, COUNT(*) FROM accounts_user GROUP BY is_verified")
    verification_counts = dict(cursor.fetchall())
    
    # Get users by staff status
    cursor.execute("SELECT is_staff, COUNT(*) FROM accounts_user GROUP BY is_staff")
    staff_counts = dict(cursor.fetchall())
    
    # Get users by active status
    cursor.execute("SELECT is_active, COUNT(*) FROM accounts_user GROUP BY is_active")
    active_counts = dict(cursor.fetchall())
    
    # Get sample users
    cursor.execute("""
        SELECT username, first_name, last_name, role, email, phone_number, city, state
        FROM accounts_user 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    sample_users = cursor.fetchall()
    
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
    
    conn.close()
    
    # Display results
    print(f"📊 User Statistics:")
    print(f"  • Total Users: {total_users}")
    print(f"  • Sales Representatives: {role_counts.get('sales_rep', 0)}")
    print(f"  • Pharmacist/Admin: {role_counts.get('pharmacist_admin', 0)}")
    print(f"  • Admin Users: {role_counts.get('admin', 0)}")
    print()
    
    print(f"👥 Profile Statistics:")
    print(f"  • Sales Rep Profiles: {sales_rep_profiles}")
    print(f"  • Pharmacist Profiles: {pharmacist_profiles}")
    print(f"  • Total Sessions: {total_sessions}")
    print(f"  • Active Sessions: {active_sessions}")
    print()
    
    print(f"✅ Verification Status:")
    print(f"  • Verified Users: {verification_counts.get(1, 0)}")
    print(f"  • Unverified Users: {verification_counts.get(0, 0)}")
    print(f"  • Staff Users: {staff_counts.get(1, 0)}")
    print(f"  • Non-Staff Users: {staff_counts.get(0, 0)}")
    print(f"  • Active Users: {active_counts.get(1, 0)}")
    print(f"  • Inactive Users: {active_counts.get(0, 0)}")
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
    
    print(f"👤 Sample Users (Latest 10):")
    for user in sample_users:
        username, first_name, last_name, role, email, phone, city, state = user
        print(f"  • {first_name} {last_name} ({username}) - {role} - {city}, {state}")
    print()
    
    print("✅ User verification complete!")
    print("🔐 All users have default password: 'password123'")
    print("📝 Users are ready for login and testing!")

if __name__ == "__main__":
    verify_users()
