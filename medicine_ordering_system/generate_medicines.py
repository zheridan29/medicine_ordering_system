#!/usr/bin/env python3
"""
Medicine Generation Script for Medicine Ordering System
Creates 5 medicines with all associated data across all related tables
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

def generate_medicines():
    """Generate 5 medicines with all associated data"""
    
    # Connect to database
    db_path = 'db.sqlite3'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 Starting Medicine Generation...")
    print("=" * 50)
    
    # Medicine data
    medicines_data = [
        {
            'name': 'Paracetamol 500mg',
            'generic_name': 'Acetaminophen',
            'description': 'Pain reliever and fever reducer. Used to treat mild to moderate pain and reduce fever.',
            'dosage_form': 'Tablet',
            'strength': '500mg',
            'prescription_type': 'otc',
            'unit_price': 0.25,
            'cost_price': 0.15,
            'current_stock': 10000,
            'minimum_stock_level': 50,
            'maximum_stock_level': 10000,
            'reorder_point': 100,
            'weight': 0.5,
            'dimensions': '10x5x3mm',
            'storage_conditions': 'Store at room temperature, away from moisture',
            'ndc_number': '12345-678-90',
            'fda_approval_date': '2020-01-15',
            'expiry_date': '2026-12-31',
            'requires_prescription': False,
            'category_name': 'Pain Relief',
            'manufacturer_name': 'MediCorp Pharmaceuticals'
        },
        {
            'name': 'Vitamin C 1000mg',
            'generic_name': 'Ascorbic Acid',
            'description': 'Essential vitamin for immune system support and antioxidant protection.',
            'dosage_form': 'Tablet',
            'strength': '1000mg',
            'prescription_type': 'otc',
            'unit_price': 0.45,
            'cost_price': 0.25,
            'current_stock': 10000,
            'minimum_stock_level': 30,
            'maximum_stock_level': 10000,
            'reorder_point': 60,
            'weight': 1.2,
            'dimensions': '12x6x4mm',
            'storage_conditions': 'Store in cool, dry place away from light',
            'ndc_number': '23456-789-01',
            'fda_approval_date': '2019-03-20',
            'expiry_date': '2025-06-30',
            'requires_prescription': False,
            'category_name': 'Vitamins & Supplements',
            'manufacturer_name': 'VitaLife Industries'
        },
        {
            'name': 'Amoxicillin 250mg',
            'generic_name': 'Amoxicillin',
            'description': 'Antibiotic used to treat various bacterial infections including respiratory and urinary tract infections.',
            'dosage_form': 'Capsule',
            'strength': '250mg',
            'prescription_type': 'prescription',
            'unit_price': 1.20,
            'cost_price': 0.80,
            'current_stock': 10000,
            'minimum_stock_level': 25,
            'maximum_stock_level': 10000,
            'reorder_point': 50,
            'weight': 0.3,
            'dimensions': '15x8x5mm',
            'storage_conditions': 'Store at room temperature, protect from moisture',
            'ndc_number': '34567-890-12',
            'fda_approval_date': '2018-07-10',
            'expiry_date': '2025-03-15',
            'requires_prescription': True,
            'category_name': 'Antibiotics',
            'manufacturer_name': 'AntibioMed Solutions'
        },
        {
            'name': 'Metformin 500mg',
            'generic_name': 'Metformin Hydrochloride',
            'description': 'Oral diabetes medication used to control blood sugar levels in type 2 diabetes.',
            'dosage_form': 'Tablet',
            'strength': '500mg',
            'prescription_type': 'prescription',
            'unit_price': 0.85,
            'cost_price': 0.55,
            'current_stock': 10000,
            'minimum_stock_level': 20,
            'maximum_stock_level': 10000,
            'reorder_point': 40,
            'weight': 0.7,
            'dimensions': '11x6x4mm',
            'storage_conditions': 'Store at room temperature, away from moisture and heat',
            'ndc_number': '45678-901-23',
            'fda_approval_date': '2017-11-05',
            'expiry_date': '2025-09-20',
            'requires_prescription': True,
            'category_name': 'Diabetes Management',
            'manufacturer_name': 'DiabetoCare Pharmaceuticals'
        },
        {
            'name': 'Ibuprofen 400mg',
            'generic_name': 'Ibuprofen',
            'description': 'Nonsteroidal anti-inflammatory drug (NSAID) used to relieve pain, reduce inflammation, and lower fever.',
            'dosage_form': 'Tablet',
            'strength': '400mg',
            'prescription_type': 'otc',
            'unit_price': 0.35,
            'cost_price': 0.20,
            'current_stock': 10000,
            'minimum_stock_level': 40,
            'maximum_stock_level': 10000,
            'reorder_point': 80,
            'weight': 0.6,
            'dimensions': '13x7x4mm',
            'storage_conditions': 'Store at room temperature, protect from light',
            'ndc_number': '56789-012-34',
            'fda_approval_date': '2019-05-12',
            'expiry_date': '2026-08-10',
            'requires_prescription': False,
            'category_name': 'Pain Relief',
            'manufacturer_name': 'PainFree Medical'
        }
    ]
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("🧹 Clearing existing medicine data...")
    cursor.execute("DELETE FROM inventory_medicineimage")
    cursor.execute("DELETE FROM inventory_reorderalert")
    cursor.execute("DELETE FROM inventory_stockmovement")
    cursor.execute("DELETE FROM inventory_medicine")
    cursor.execute("DELETE FROM inventory_manufacturer")
    cursor.execute("DELETE FROM inventory_category")
    conn.commit()
    print("✅ Existing medicine data cleared")
    
    # Generate categories
    print("\n📂 Creating Categories...")
    categories = {}
    category_data = [
        {'name': 'Pain Relief', 'description': 'Medicines for pain management and relief'},
        {'name': 'Vitamins & Supplements', 'description': 'Essential vitamins and dietary supplements'},
        {'name': 'Antibiotics', 'description': 'Medicines to treat bacterial infections'},
        {'name': 'Diabetes Management', 'description': 'Medicines for diabetes control and management'},
        {'name': 'Cardiovascular', 'description': 'Medicines for heart and blood vessel conditions'},
        {'name': 'Respiratory', 'description': 'Medicines for breathing and lung conditions'},
        {'name': 'Digestive Health', 'description': 'Medicines for digestive system health'},
        {'name': 'Mental Health', 'description': 'Medicines for mental health conditions'}
    ]
    
    for i, cat_data in enumerate(category_data, 1):
        cursor.execute("""
            INSERT INTO inventory_category (id, name, description, parent_category_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            i,
            cat_data['name'],
            cat_data['description'],
            None,
            True,
            datetime.now().isoformat()
        ))
        categories[cat_data['name']] = i
        print(f"  ✅ Created category: {cat_data['name']}")
    
    # Generate manufacturers
    print("\n🏭 Creating Manufacturers...")
    manufacturers = {}
    manufacturer_data = [
        {
            'name': 'MediCorp Pharmaceuticals',
            'country': 'United States',
            'contact_email': 'info@medicorp.com',
            'contact_phone': '+1-555-0101',
            'website': 'https://www.medicorp.com'
        },
        {
            'name': 'VitaLife Industries',
            'country': 'Canada',
            'contact_email': 'contact@vitalife.ca',
            'contact_phone': '+1-555-0102',
            'website': 'https://www.vitalife.ca'
        },
        {
            'name': 'AntibioMed Solutions',
            'country': 'Germany',
            'contact_email': 'info@antibiomed.de',
            'contact_phone': '+49-555-0103',
            'website': 'https://www.antibiomed.de'
        },
        {
            'name': 'DiabetoCare Pharmaceuticals',
            'country': 'United States',
            'contact_email': 'support@diabetocare.com',
            'contact_phone': '+1-555-0104',
            'website': 'https://www.diabetocare.com'
        },
        {
            'name': 'PainFree Medical',
            'country': 'United Kingdom',
            'contact_email': 'info@painfree.co.uk',
            'contact_phone': '+44-555-0105',
            'website': 'https://www.painfree.co.uk'
        }
    ]
    
    for i, man_data in enumerate(manufacturer_data, 1):
        cursor.execute("""
            INSERT INTO inventory_manufacturer (id, name, country, contact_email, contact_phone, website, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i,
            man_data['name'],
            man_data['country'],
            man_data['contact_email'],
            man_data['contact_phone'],
            man_data['website'],
            True,
            datetime.now().isoformat()
        ))
        manufacturers[man_data['name']] = i
        print(f"  ✅ Created manufacturer: {man_data['name']}")
    
    # Generate medicines
    print("\n💊 Creating Medicines...")
    medicines_created = 0
    stock_movements_created = 0
    reorder_alerts_created = 0
    
    for i, med_data in enumerate(medicines_data, 1):
        # Create medicine
        cursor.execute("""
            INSERT INTO inventory_medicine (
                id, name, generic_name, description, category_id, manufacturer_id,
                dosage_form, strength, prescription_type, unit_price, cost_price,
                current_stock, minimum_stock_level, maximum_stock_level, reorder_point,
                weight, dimensions, storage_conditions, ndc_number, fda_approval_date,
                expiry_date, is_active, is_available, requires_prescription, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            i,
            med_data['name'],
            med_data['generic_name'],
            med_data['description'],
            categories[med_data['category_name']],
            manufacturers[med_data['manufacturer_name']],
            med_data['dosage_form'],
            med_data['strength'],
            med_data['prescription_type'],
            str(med_data['unit_price']),
            str(med_data['cost_price']),
            med_data['current_stock'],
            med_data['minimum_stock_level'],
            med_data['maximum_stock_level'],
            med_data['reorder_point'],
            str(med_data['weight']),
            med_data['dimensions'],
            med_data['storage_conditions'],
            med_data['ndc_number'],
            med_data['fda_approval_date'],
            med_data['expiry_date'],
            True,
            True,
            med_data['requires_prescription'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        medicines_created += 1
        print(f"  ✅ Created medicine: {med_data['name']}")
        
        # Create initial stock movement (stock in) - get next available ID
        cursor.execute("SELECT MAX(id) FROM inventory_stockmovement")
        max_id = cursor.fetchone()[0] or 0
        next_id = max_id + 1
        
        cursor.execute("""
            INSERT INTO inventory_stockmovement (
                id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            next_id,
            i,
            'in',
            med_data['current_stock'],
            f'INIT-{med_data["ndc_number"]}',
            f'Initial stock for {med_data["name"]}',
            1,  # Assuming user ID 1 exists
            datetime.now().isoformat()
        ))
        stock_movements_created += 1
        
        # Create some additional stock movements for realism
        for j in range(random.randint(2, 5)):
            movement_types = ['in', 'out', 'adjustment']
            movement_type = random.choice(movement_types)
            quantity = random.randint(10, 100) if movement_type == 'in' else random.randint(1, 50)
            if movement_type == 'out':
                quantity = -quantity
            
            # Get next available ID
            cursor.execute("SELECT MAX(id) FROM inventory_stockmovement")
            max_id = cursor.fetchone()[0] or 0
            next_id = max_id + 1
            
            cursor.execute("""
                INSERT INTO inventory_stockmovement (
                    id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                next_id,
                i,
                movement_type,
                quantity,
                f'REF-{random.randint(1000, 9999)}',
                f'{movement_type.title()} movement for {med_data["name"]}',
                1,
                (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            ))
            stock_movements_created += 1
        
        # Create reorder alert if stock is low
        if med_data['current_stock'] <= med_data['reorder_point']:
            suggested_quantity = med_data['maximum_stock_level'] - med_data['current_stock']
            priority = 'urgent' if med_data['current_stock'] < med_data['minimum_stock_level'] else 'medium'
            
            cursor.execute("""
                INSERT INTO inventory_reorderalert (
                    id, medicine_id, current_stock, reorder_point, suggested_quantity, priority, is_processed, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                i,
                i,
                med_data['current_stock'],
                med_data['reorder_point'],
                suggested_quantity,
                priority,
                False,
                datetime.now().isoformat()
            ))
            reorder_alerts_created += 1
            print(f"    ⚠️  Created reorder alert for {med_data['name']} (Priority: {priority})")
    
    # Create some additional stock movements for all medicines
    print("\n📦 Creating Additional Stock Movements...")
    for medicine_id in range(1, medicines_created + 1):
        for j in range(random.randint(3, 8)):
            movement_types = ['in', 'out', 'adjustment', 'return', 'damage']
            movement_type = random.choice(movement_types)
            quantity = random.randint(5, 50)
            if movement_type in ['out', 'damage']:
                quantity = -quantity
            
            # Get next available ID
            cursor.execute("SELECT MAX(id) FROM inventory_stockmovement")
            max_id = cursor.fetchone()[0] or 0
            next_id = max_id + 1
            
            cursor.execute("""
                INSERT INTO inventory_stockmovement (
                    id, medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                next_id,
                medicine_id,
                movement_type,
                quantity,
                f'REF-{random.randint(1000, 9999)}',
                f'{movement_type.title()} movement - {random.choice(["Regular restock", "Customer return", "Quality adjustment", "Damaged goods", "Expired items"])}',
                1,
                (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat()
            ))
            stock_movements_created += 1
    
    # Create some reorder alerts for medicines that might need restocking
    print("\n⚠️  Creating Additional Reorder Alerts...")
    for medicine_id in range(1, medicines_created + 1):
        if random.choice([True, False]):  # 50% chance of having a reorder alert
            cursor.execute("SELECT current_stock, reorder_point, maximum_stock_level FROM inventory_medicine WHERE id = ?", (medicine_id,))
            stock_data = cursor.fetchone()
            if stock_data:
                current_stock, reorder_point, max_stock = stock_data
                suggested_quantity = max_stock - current_stock
                priority = random.choice(['low', 'medium', 'high'])
                
                cursor.execute("""
                    INSERT INTO inventory_reorderalert (
                        id, medicine_id, current_stock, reorder_point, suggested_quantity, priority, is_processed, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reorder_alerts_created + 1,
                    medicine_id,
                    current_stock,
                    reorder_point,
                    suggested_quantity,
                    priority,
                    random.choice([True, False]),
                    (datetime.now() - timedelta(days=random.randint(1, 7))).isoformat()
                ))
                reorder_alerts_created += 1
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("🎉 Medicine Generation Complete!")
    print("=" * 50)
    print(f"📊 Summary:")
    print(f"  • Categories Created: {len(categories)}")
    print(f"  • Manufacturers Created: {len(manufacturers)}")
    print(f"  • Medicines Created: {medicines_created}")
    print(f"  • Stock Movements Created: {stock_movements_created}")
    print(f"  • Reorder Alerts Created: {reorder_alerts_created}")
    print(f"  • Database: {db_path}")
    print("\n✅ All medicines and associated data are ready!")
    print("💊 Medicines include:")
    for med in medicines_data:
        print(f"  • {med['name']} - {med['category_name']} - ${med['unit_price']}")
    print("\n📦 Complete inventory system with stock tracking, alerts, and movements!")

if __name__ == "__main__":
    generate_medicines()
