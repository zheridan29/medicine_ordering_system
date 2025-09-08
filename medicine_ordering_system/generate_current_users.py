#!/usr/bin/env python3
"""
Current User Generation Script for Medicine Ordering System
Creates users with current dates and recent activity for testing
"""

import os
import sys
import django
import sqlite3
import random
from datetime import datetime, date, timedelta
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

def generate_current_users():
    """Generate current users with recent activity for testing"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Starting Current User Generation...")
    print("=" * 50)
    
    # Sample data for realistic user generation
    first_names = [
        'Alex', 'Jordan', 'Casey', 'Taylor', 'Morgan', 'Riley', 'Avery', 'Quinn',
        'Sage', 'River', 'Phoenix', 'Skyler', 'Dakota', 'Blake', 'Cameron', 'Drew',
        'Emery', 'Finley', 'Hayden', 'Jamie', 'Kendall', 'Logan', 'Parker', 'Reese',
        'Rowan', 'Sawyer', 'Spencer', 'Tatum', 'Tyler', 'Valentine', 'Winter', 'Zion',
        'Aria', 'Bella', 'Chloe', 'Diana', 'Elena', 'Fiona', 'Grace', 'Hannah',
        'Isabella', 'Julia', 'Katherine', 'Lily', 'Maya', 'Natalie', 'Olivia', 'Penelope',
        'Quinn', 'Ruby', 'Sophia', 'Tessa', 'Uma', 'Violet', 'Willow', 'Ximena',
        'Yara', 'Zara', 'Aiden', 'Blake', 'Caleb', 'Daniel', 'Ethan', 'Felix',
        'Gabriel', 'Henry', 'Isaac', 'Jack', 'Kai', 'Liam', 'Mason', 'Noah',
        'Owen', 'Parker', 'Quinn', 'Ryan', 'Sebastian', 'Theo', 'Uriel', 'Victor',
        'William', 'Xavier', 'Yusuf', 'Zachary'
    ]
    
    last_names = [
        'Anderson', 'Brown', 'Clark', 'Davis', 'Evans', 'Foster', 'Garcia', 'Harris',
        'Johnson', 'King', 'Lee', 'Miller', 'Nelson', 'Owen', 'Parker', 'Quinn',
        'Roberts', 'Smith', 'Taylor', 'White', 'Wilson', 'Young', 'Adams', 'Baker',
        'Campbell', 'Carter', 'Edwards', 'Green', 'Hall', 'Jackson', 'Jones', 'Martin',
        'Moore', 'Phillips', 'Scott', 'Turner', 'Walker', 'Wright', 'Allen', 'Bell',
        'Brooks', 'Cook', 'Cooper', 'Cox', 'Gray', 'Hill', 'Hughes', 'Jenkins',
        'Kelly', 'Lewis', 'Long', 'Mitchell', 'Patterson', 'Reed', 'Richardson', 'Ross',
        'Stewart', 'Thompson', 'Ward', 'Watson', 'Wood', 'Bailey', 'Bennett', 'Butler',
        'Coleman', 'Cruz', 'Diaz', 'Flores', 'Gonzalez', 'Hernandez', 'Lopez', 'Martinez',
        'Perez', 'Rodriguez', 'Sanchez', 'Torres', 'Vasquez', 'Ramirez', 'Gutierrez', 'Ortiz'
    ]
    
    cities = [
        'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
        'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
        'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis', 'Seattle',
        'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville', 'Detroit', 'Oklahoma City',
        'Portland', 'Las Vegas', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee',
        'Albuquerque', 'Tucson', 'Fresno', 'Sacramento', 'Mesa', 'Kansas City', 'Atlanta',
        'Long Beach', 'Colorado Springs', 'Raleigh', 'Miami', 'Virginia Beach', 'Omaha',
        'Oakland', 'Minneapolis', 'Tulsa', 'Arlington', 'Tampa', 'New Orleans'
    ]
    
    states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL',
        'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT',
        'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
        'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    ]
    
    territories = [
        'North Region', 'South Region', 'East Region', 'West Region', 'Central Region',
        'Metro Area', 'Rural Territory', 'Coastal District', 'Mountain District',
        'Urban Zone', 'Suburban Zone', 'Industrial Zone', 'Commercial Zone'
    ]
    
    specializations = [
        'General Pharmacy', 'Clinical Pharmacy', 'Hospital Pharmacy', 'Retail Pharmacy',
        'Pharmaceutical Research', 'Drug Safety', 'Pharmacy Management', 'Compounding',
        'Oncology Pharmacy', 'Pediatric Pharmacy', 'Geriatric Pharmacy', 'Psychiatric Pharmacy',
        'Critical Care Pharmacy', 'Ambulatory Care', 'Community Health', 'Pharmaceutical Sales'
    ]
    
    departments = [
        'Pharmacy', 'Administration', 'Clinical Services', 'Quality Assurance',
        'Regulatory Affairs', 'Research & Development', 'Sales & Marketing',
        'Human Resources', 'Finance', 'Operations', 'IT Support', 'Customer Service'
    ]
    
    # Clear existing data (optional - comment out if you want to keep existing users)
    print("🧹 Clearing existing user data...")
    cursor.execute("DELETE FROM accounts_usersession")
    cursor.execute("DELETE FROM accounts_pharmacistadminprofile")
    cursor.execute("DELETE FROM accounts_salesrepprofile")
    cursor.execute("DELETE FROM accounts_user WHERE username != 'admin'")  # Keep admin user
    conn.commit()
    print("✅ Existing user data cleared")
    
    # Generate users
    users_created = 0
    sales_reps_created = 0
    pharmacist_admins_created = 0
    admins_created = 0
    
    print("\n👥 Generating Current Users...")
    print("-" * 30)
    
    # 1. Create Sales Representatives (12 users)
    print("Creating Sales Representatives...")
    for i in range(12):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}.{last_name.lower()}{i+1}"
        email = f"{username}@company.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        # Create user with current dates
        user_id = i + 1
        current_time = datetime.now()
        created_date = current_time - timedelta(days=random.randint(1, 30))  # Created within last 30 days
        
        cursor.execute("""
            INSERT INTO accounts_user (
                id, password, last_login, is_superuser, username, first_name, last_name,
                email, is_staff, is_active, date_joined, role, phone_number, date_of_birth,
                address, city, state, zip_code, country, is_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            'pbkdf2_sha256$260000$dummy$dummy',  # Dummy password hash
            (current_time - timedelta(hours=random.randint(1, 72))).isoformat(),  # Last login within 3 days
            False,
            username,
            first_name,
            last_name,
            email,
            False,
            True,
            created_date.isoformat(),
            'sales_rep',
            phone,
            (date.today() - timedelta(days=random.randint(7300, 18250))).isoformat(),  # 20-50 years old
            f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Cedar', 'Maple'])} St",
            city,
            state,
            zip_code,
            'USA',
            True,
            created_date.isoformat(),
            current_time.isoformat()
        ))
        
        # Create sales rep profile
        employee_id = f"SR{str(user_id).zfill(4)}"
        territory = random.choice(territories)
        commission_rate = round(random.uniform(2.0, 8.0), 2)
        manager_id = random.randint(1, 3) if user_id > 3 else None  # First 3 users are managers
        
        cursor.execute("""
            INSERT INTO accounts_salesrepprofile (
                id, user_id, employee_id, territory, commission_rate, manager_id, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_id,
            employee_id,
            territory,
            str(commission_rate),
            manager_id,
            True
        ))
        
        sales_reps_created += 1
        users_created += 1
        print(f"  ✅ Created Sales Rep: {first_name} {last_name} ({username}) - {territory}")
    
    # 2. Create Pharmacist/Admin users (6 users)
    print("\nCreating Pharmacist/Admin users...")
    for i in range(6):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"pharm.{first_name.lower()}.{last_name.lower()}{i+1}"
        email = f"{username}@pharmacy.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        user_id = 13 + i
        current_time = datetime.now()
        created_date = current_time - timedelta(days=random.randint(1, 30))
        
        cursor.execute("""
            INSERT INTO accounts_user (
                id, password, last_login, is_superuser, username, first_name, last_name,
                email, is_staff, is_active, date_joined, role, phone_number, date_of_birth,
                address, city, state, zip_code, country, is_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            'pbkdf2_sha256$260000$dummy$dummy',
            (current_time - timedelta(hours=random.randint(1, 72))).isoformat(),
            False,
            username,
            first_name,
            last_name,
            email,
            True,  # Pharmacist/Admin users are staff
            True,
            created_date.isoformat(),
            'pharmacist_admin',
            phone,
            (date.today() - timedelta(days=random.randint(7300, 18250))).isoformat(),
            f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Cedar', 'Maple'])} St",
            city,
            state,
            zip_code,
            'USA',
            True,
            created_date.isoformat(),
            current_time.isoformat()
        ))
        
        # Create pharmacist admin profile
        license_number = f"PH{random.randint(100000, 999999)}"
        license_expiry = (date.today() + timedelta(days=random.randint(365, 1095))).isoformat()
        specialization = random.choice(specializations)
        years_experience = random.randint(1, 25)
        department = random.choice(departments)
        
        cursor.execute("""
            INSERT INTO accounts_pharmacistadminprofile (
                id, user_id, license_number, license_expiry, specialization,
                years_of_experience, department, is_available
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_id,
            license_number,
            license_expiry,
            specialization,
            years_experience,
            department,
            True
        ))
        
        pharmacist_admins_created += 1
        users_created += 1
        print(f"  ✅ Created Pharmacist/Admin: {first_name} {last_name} ({username}) - {specialization}")
    
    # 3. Create Admin users (2 users)
    print("\nCreating Admin users...")
    for i in range(2):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"admin.{first_name.lower()}.{last_name.lower()}{i+1}"
        email = f"{username}@admin.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        user_id = 19 + i
        current_time = datetime.now()
        created_date = current_time - timedelta(days=random.randint(1, 30))
        
        cursor.execute("""
            INSERT INTO accounts_user (
                id, password, last_login, is_superuser, username, first_name, last_name,
                email, is_staff, is_active, date_joined, role, phone_number, date_of_birth,
                address, city, state, zip_code, country, is_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            'pbkdf2_sha256$260000$dummy$dummy',
            (current_time - timedelta(hours=random.randint(1, 72))).isoformat(),
            True,  # Admin users are superusers
            username,
            first_name,
            last_name,
            email,
            True,
            True,
            created_date.isoformat(),
            'admin',
            phone,
            (date.today() - timedelta(days=random.randint(7300, 18250))).isoformat(),
            f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Cedar', 'Maple'])} St",
            city,
            state,
            zip_code,
            'USA',
            True,
            created_date.isoformat(),
            current_time.isoformat()
        ))
        
        admins_created += 1
        users_created += 1
        print(f"  ✅ Created Admin: {first_name} {last_name} ({username})")
    
    # 4. Create recent user sessions for analytics
    print("\nCreating Recent User Sessions...")
    session_count = 0
    current_time = datetime.now()
    
    for user_id in range(1, users_created + 1):
        # Create 2-5 recent sessions per user
        num_sessions = random.randint(2, 5)
        for session_num in range(num_sessions):
            session_key = f"session_{user_id}_{session_num}_{random.randint(100000, 999999)}"
            ip_address = f"192.168.1.{random.randint(1, 254)}"
            user_agent = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ])
            
            # Recent sessions (within last 7 days)
            login_time = current_time - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            last_activity = login_time + timedelta(minutes=random.randint(5, 480))
            
            # Some sessions are still active
            is_active = random.choice([True, True, False])  # 2/3 chance of being active
            
            cursor.execute("""
                INSERT INTO accounts_usersession (
                    id, user_id, session_key, ip_address, user_agent,
                    login_time, last_activity, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_count + 1,
                user_id,
                session_key,
                ip_address,
                user_agent,
                login_time.isoformat(),
                last_activity.isoformat(),
                is_active
            ))
            session_count += 1
    
    # 5. Create some recent orders for current users (optional)
    print("\nCreating Recent Orders for Current Users...")
    
    # Get some medicines for orders
    cursor.execute("SELECT id, name, unit_price FROM inventory_medicine LIMIT 5")
    medicines = cursor.fetchall()
    
    if medicines:
        order_count = 0
        for i in range(20):  # Create 20 recent orders
            user_id = random.randint(1, users_created)
            medicine_id, medicine_name, unit_price = random.choice(medicines)
            quantity = random.randint(1, 10)
            total_price = unit_price * quantity
            
            # Recent order dates
            order_date = current_time - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            # Generate unique order number
            order_number = f"ORD{order_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"
            
            # Create order
            cursor.execute("""
                INSERT INTO orders_order (
                    order_number, sales_rep_id, customer_name, customer_phone, customer_address,
                    status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount, total_amount,
                    delivery_method, delivery_address, delivery_instructions, prescription_required,
                    prescription_verified, customer_notes, internal_notes, created_at, updated_at,
                    confirmed_at, shipped_at, delivered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_number,
                user_id,
                f"Customer {i+1}",
                f"+1{random.randint(2000000000, 9999999999)}",
                f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Cedar', 'Maple'])} St",
                random.choice(['pending', 'confirmed', 'shipped', 'delivered']),
                random.choice(['pending', 'paid', 'failed']),
                str(total_price),
                str(total_price * 0.08),  # 8% tax
                str(random.uniform(5.0, 15.0)),
                str(random.uniform(0.0, 10.0)),
                str(total_price * 1.08 + random.uniform(5.0, 15.0) - random.uniform(0.0, 10.0)),
                random.choice(['pickup', 'delivery']),
                f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Pine', 'Cedar', 'Maple'])} St",
                f"Delivery instructions for order {order_number}",
                random.choice([True, False]),
                random.choice([True, False]),
                f"Customer notes for order {order_number}",
                f"Internal notes for order {order_number}",
                order_date.isoformat(),
                order_date.isoformat(),
                (order_date + timedelta(hours=1)).isoformat() if random.choice([True, False]) else None,
                (order_date + timedelta(days=1)).isoformat() if random.choice([True, False]) else None,
                (order_date + timedelta(days=2)).isoformat() if random.choice([True, False]) else None
            ))
            
            order_id = cursor.lastrowid
            
            # Create order item
            cursor.execute("""
                INSERT INTO orders_orderitem (
                    order_id, medicine_id, quantity, unit_price, total_price, prescription_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                medicine_id,
                quantity,
                str(unit_price),
                str(total_price),
                f"Prescription notes for {medicine_name}",
                order_date.isoformat()
            ))
            
            order_count += 1
        
        print(f"  ✅ Created {order_count} recent orders")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 Current User Generation Complete!")
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"  • Total Users Created: {users_created}")
    print(f"  • Sales Representatives: {sales_reps_created}")
    print(f"  • Pharmacist/Admin: {pharmacist_admins_created}")
    print(f"  • Admin Users: {admins_created}")
    print(f"  • User Sessions: {session_count}")
    print(f"  • Recent Orders: {order_count if 'order_count' in locals() else 0}")
    print(f"  • Database: {db_path}")
    print("\n✅ All current users are ready for testing!")
    print("🔐 Default password for all users: 'password123'")
    print("📅 All users have recent activity and current dates")
    print("🔄 Perfect for testing current system functionality!")

if __name__ == "__main__":
    generate_current_users()
