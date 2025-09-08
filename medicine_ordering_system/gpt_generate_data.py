#!/usr/bin/env python
"""
Generate historical transactional data (2020–2024) for medicines created in generate_medicines.py
- Uses direct SQL to ensure historical dates (no Django timezone handling)
- Respects stock limits (no overselling)
- Produces realistic seasonal demand patterns
- Useful for ARIMA testing on medicine sales data
"""

import os
import django
from datetime import datetime, date, timedelta
import random
import sqlite3

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medicine_ordering_system.settings")
django.setup()

from django.db import connection
from inventory.models import Medicine
from accounts.models import User


# --- DB Helpers ---
def get_database_path():
    from django.conf import settings
    return settings.DATABASES["default"]["NAME"]

def get_current_stock(medicine_id):
    """Get the latest stock level from DB"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT current_stock FROM inventory_medicine WHERE id = ?", (medicine_id,))
    stock = cursor.fetchone()[0]
    conn.close()
    return stock


# --- Order Generation ---
def create_historical_orders(medicine, sales_rep_id, customer_ids, start_year=2020, end_year=2024):
    """Generate historical orders for a given medicine within stock limits"""

    med_id, name, generic, unit_price, stock, prescription_type, category_id = medicine
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    orders_created = 0
    remaining_stock = stock  # prevent overselling

    print(f"📦 Generating orders for {name} (Stock: {stock})...")

    current_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)

    while current_date <= end_date and remaining_stock > 0:
        # Seasonal patterns (simple: vitamins higher in winter, antibiotics in flu season, etc.)
        month = current_date.month
        base_demand = 1

        if "vitamin" in name.lower():
            seasonal_multiplier = 1.5 if month in [1, 2, 11, 12] else 0.7
        elif "antibiotic" in name.lower() or "amoxicillin" in name.lower():
            seasonal_multiplier = 1.3 if month in [1, 2, 11, 12] else 0.8
        else:
            seasonal_multiplier = 1.0

        # Daily demand simulation
        daily_orders = max(0, int(random.gauss(base_demand * seasonal_multiplier, 0.5)))

        for _ in range(daily_orders):
            if remaining_stock <= 0:
                break

            customer_id = random.choice(customer_ids)

            # Order quantity (1–5, limited by stock left)
            max_qty = min(5, remaining_stock)
            qty = random.randint(1, max_qty)

            # Prices & costs
            subtotal = unit_price * qty
            tax = subtotal * 0.08
            shipping = 0 if subtotal > 50 else 5.99
            discount = subtotal * 0.05 if qty >= 5 else 0.0
            total = subtotal + tax + shipping - discount

            # Order timestamps
            order_dt = datetime.combine(current_date, datetime.min.time())
            order_no = f"ORD{current_date.strftime('%Y%m%d')}{random.randint(1000, 9999)}"

            # Insert order
            cursor.execute("""
                INSERT INTO orders_order (
                    order_number, sales_rep_id, customer_name, customer_phone, customer_address,
                    status, payment_status, subtotal, tax_amount, shipping_cost, discount_amount,
                    total_amount, delivery_method, delivery_address, delivery_instructions,
                    prescription_required, prescription_verified, customer_notes, internal_notes,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order_no, sales_rep_id, f"Customer {customer_id}", "+1-555-0000", "123 Main St",
                "delivered", "paid", str(subtotal), str(tax), str(shipping), str(discount),
                str(total), "delivery", "123 Main St", f"Handle {name} with care",
                "prescription" in name.lower(), False, "Customer note", "System generated",
                order_dt.isoformat(), order_dt.isoformat()
            ))

            order_id = cursor.lastrowid

            # Insert order item
            cursor.execute("""
                INSERT INTO orders_orderitem (
                    order_id, medicine_id, quantity, unit_price, total_price, prescription_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order_id, med_id, qty, str(unit_price), str(subtotal), f"Notes for {name}", order_dt.isoformat()
            ))

            # Insert stock movement
            cursor.execute("""
                INSERT INTO inventory_stockmovement (
                    medicine_id, movement_type, quantity, reference_number, notes, created_by_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                med_id, "out", -qty, order_no, f"Sale of {name}", sales_rep_id, order_dt.isoformat()
            ))

            # Deduct stock
            remaining_stock -= qty
            orders_created += 1

        current_date += timedelta(days=1)

    conn.commit()
    conn.close()
    print(f"✅ {orders_created} orders created for {name} (Final stock: {remaining_stock})")
    return orders_created


# --- MAIN ---
def main():
    print("=== HISTORICAL DATA GENERATOR ===")

    # Get medicines
    medicines = list(Medicine.objects.filter(is_active=True, is_available=True)
                     .values_list("id", "name", "generic_name", "unit_price", "current_stock", "prescription_type", "category_id"))

    if not medicines:
        print("❌ No medicines found. Run generate_medicines.py first.")
        return

    # Sales rep
    try:
        sales_rep = User.objects.filter(role="sales_rep").first()
        if not sales_rep:
            raise User.DoesNotExist
    except User.DoesNotExist:
        print("❌ No sales rep found. Create one first.")
        return

    # Customers
    customers = list(User.objects.filter(role="customer").values_list("id", flat=True))
    if not customers:
        print("❌ No customers found. Create some customers first.")
        return

    # Clear old data
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM orders_orderitem")
        cursor.execute("DELETE FROM orders_order")
        cursor.execute("DELETE FROM inventory_stockmovement WHERE movement_type = 'out'")
    print("🗑️ Old orders cleared.")

    total_orders = 0
    for med in medicines:
        total_orders += create_historical_orders(med, sales_rep.id, customers)

    print("\n=== SUMMARY ===")
    print(f"📊 Total orders generated: {total_orders}")
    print("📅 Date range: 2020–2024")
    print("✅ Stock limits respected")
    print("✅ Ready for ARIMA testing")


if __name__ == "__main__":
    main()
