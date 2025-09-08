#!/usr/bin/env python3
"""
Matching User Generation Script for Medicine Ordering System
Creates users that match the existing database pattern
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

def generate_matching_users():
    """Generate users that match the existing database pattern"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Starting Matching User Generation...")
    print("=" * 50)
    
    # Customer user patterns (based on existing data)
    customer_patterns = [
        'wellness_coach', 'healthcare_worker', 'athlete', 'retiree', 'college_student',
        'family_mom', 'busy_professional', 'fitness_trainer', 'senior_citizen', 'health_enthusiast',
        'yoga_instructor', 'nutritionist', 'personal_trainer', 'medical_student', 'pharmacy_tech',
        'nurse_practitioner', 'physical_therapist', 'dietitian', 'health_coach', 'wellness_advisor',
        'fitness_enthusiast', 'health_researcher', 'medical_writer', 'health_blogger', 'wellness_expert',
        'chronic_patient', 'diabetes_management', 'heart_health', 'mental_health', 'elderly_care',
        'pediatric_care', 'women_health', 'men_health', 'family_health', 'community_health'
    ]
    
    # Sales rep patterns
    sales_rep_patterns = [
        'sales_rep_1', 'sales_rep_2', 'sales_rep_3', 'sales_rep_4', 'sales_rep_5',
        'sales_rep_6', 'sales_rep_7', 'sales_rep_8', 'sales_rep_9', 'sales_rep_10',
        'sales_rep_11', 'sales_rep_12', 'sales_rep_13', 'sales_rep_14', 'sales_rep_15',
        'sales_rep_16', 'sales_rep_17', 'sales_rep_18', 'sales_rep_19', 'sales_rep_20'
    ]
    
    # Pharmacist patterns
    pharmacist_patterns = [
        'pharmacist_1', 'pharmacist_2', 'pharmacist_3', 'pharmacist_4', 'pharmacist_5',
        'pharmacist_6', 'pharmacist_7', 'pharmacist_8', 'pharmacist_9', 'pharmacist_10'
    ]
    
    # Admin patterns
    admin_patterns = [
        'admin_1', 'admin_2', 'admin_3', 'admin_4', 'admin_5'
    ]
    
    # Sample data for realistic user generation
    first_names = [
        'John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Emily',
        'William', 'Jessica', 'James', 'Ashley', 'Christopher', 'Amanda', 'Daniel',
        'Jennifer', 'Matthew', 'Michelle', 'Anthony', 'Kimberly', 'Mark', 'Donna',
        'Donald', 'Carol', 'Steven', 'Sandra', 'Paul', 'Ruth', 'Andrew', 'Sharon',
        'Joshua', 'Nancy', 'Kenneth', 'Deborah', 'Kevin', 'Dorothy', 'Brian', 'Lisa',
        'George', 'Betty', 'Timothy', 'Helen', 'Ronald', 'Shirley', 'Jason', 'Brenda',
        'Edward', 'Pamela', 'Jeffrey', 'Janet', 'Ryan', 'Catherine', 'Jacob', 'Frances',
        'Gary', 'Christine', 'Nicholas', 'Samantha', 'Eric', 'Debra', 'Jonathan', 'Rachel',
        'Stephen', 'Carolyn', 'Larry', 'Janet', 'Justin', 'Virginia', 'Scott', 'Maria',
        'Brandon', 'Heather', 'Benjamin', 'Diane', 'Samuel', 'Julie', 'Gregory', 'Joyce',
        'Alexander', 'Victoria', 'Patrick', 'Kelly', 'Jack', 'Christina', 'Dennis', 'Joan',
        'Jerry', 'Evelyn', 'Tyler', 'Judith', 'Aaron', 'Megan', 'Jose', 'Cheryl',
        'Henry', 'Mildred', 'Adam', 'Katherine', 'Douglas', 'Joan', 'Nathan', 'Gloria',
        'Peter', 'Ethel', 'Zachary', 'Kathryn', 'Kyle', 'Angela', 'Noah', 'Beverly',
        'Alan', 'Doris', 'Jeremy', 'Ann', 'Ethan', 'Jean', 'Mason', 'Alice', 'Logan', 'Marie'
    ]
    
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
        'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill',
        'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell',
        'Mitchell', 'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz',
        'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales',
        'Murphy', 'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson',
        'Bailey', 'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson',
        'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza',
        'Ruiz', 'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers',
        'Long', 'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell',
        'Sullivan', 'Bell', 'Coleman', 'Butler', 'Henderson', 'Barnes', 'Gonzales',
        'Fisher', 'Vasquez', 'Simmons', 'Romero', 'Jordan', 'Patterson', 'Alexander',
        'Hamilton', 'Graham', 'Reynolds', 'Griffin', 'Wallace', 'Moreno', 'West',
        'Cole', 'Hayes', 'Bryant', 'Herrera', 'Gibson', 'Ellis', 'Tran', 'Medina',
        'Aguilar', 'Stevens', 'Murray', 'Ford', 'Castro', 'Marshall', 'Owens', 'Harrison'
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
    customers_created = 0
    sales_reps_created = 0
    pharmacist_admins_created = 0
    admins_created = 0
    
    print("\n👥 Generating Matching Users...")
    print("-" * 30)
    
    # 1. Create Customer users (10 users) - matching existing pattern
    print("Creating Customer users...")
    for i in range(10):
        username = customer_patterns[i]
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{username}@example.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        # Create user
        user_id = i + 1
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
            False,
            True,
            created_date.isoformat(),
            'customer',
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
        
        customers_created += 1
        users_created += 1
        print(f"  ✅ Created Customer: {first_name} {last_name} ({username})")
    
    # 2. Create Sales Representatives (13 users) - matching existing pattern
    print("\nCreating Sales Representatives...")
    for i in range(13):
        username = sales_rep_patterns[i]
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{username}@company.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        # Create user
        user_id = 11 + i
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
            False,
            True,
            created_date.isoformat(),
            'sales_rep',
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
        
        # Create sales rep profile
        employee_id = f"SR{str(user_id).zfill(4)}"
        territory = random.choice(territories)
        commission_rate = round(random.uniform(2.0, 8.0), 2)
        manager_id = random.randint(11, 13) if user_id > 13 else None  # First 3 sales reps are managers
        
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
    
    # 3. Create Pharmacist/Admin users (1 user) - matching existing pattern
    print("\nCreating Pharmacist/Admin users...")
    for i in range(1):
        username = pharmacist_patterns[i]
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{username}@pharmacy.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        user_id = 24
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
    
    # 4. Create Admin users (1 user) - matching existing pattern
    print("\nCreating Admin users...")
    for i in range(1):
        username = admin_patterns[i]
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{username}@admin.com"
        phone = f"+1{random.randint(2000000000, 9999999999)}"
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        
        user_id = 25
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
    
    # 5. Create user sessions for analytics
    print("\nCreating User Sessions...")
    session_count = 0
    current_time = datetime.now()
    
    for user_id in range(1, users_created + 1):
        # Create 1-3 sessions per user
        num_sessions = random.randint(1, 3)
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
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 Matching User Generation Complete!")
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"  • Total Users Created: {users_created}")
    print(f"  • Customer Users: {customers_created}")
    print(f"  • Sales Representatives: {sales_reps_created}")
    print(f"  • Pharmacist/Admin: {pharmacist_admins_created}")
    print(f"  • Admin Users: {admins_created}")
    print(f"  • User Sessions: {session_count}")
    print(f"  • Database: {db_path}")
    print("\n✅ All users match the existing database pattern!")
    print("🔐 Default password for all users: 'password123'")
    print("📝 Users follow the same naming convention as existing data")

if __name__ == "__main__":
    generate_matching_users()
