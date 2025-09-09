#!/usr/bin/env python
"""
Test script for the modified auto-forecast flow with medicine selection
"""
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from inventory.models import Medicine

def test_modified_flow():
    """Test the modified auto-forecast flow with medicine selection"""
    print("Testing Modified Auto-Forecast Flow...")
    
    # Set up Django settings for testing
    from django.conf import settings
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
    
    # Create a test client
    client = Client()
    
    # Get or create a test user
    User = get_user_model()
    user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'test@example.com',
            'role': 'admin'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("Created test user")
    else:
        print("Using existing test user")
    
    # Login the user
    login_success = client.login(username='test_admin', password='testpass123')
    if not login_success:
        print("Failed to login test user")
        return False
    
    print("Successfully logged in test user")
    
    # Test 1: API without medicine_id (should work as before)
    print("\n--- Test 1: API without medicine_id ---")
    try:
        response = client.get('/analytics/api/forecast/best-auto/')
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Auto-forecast API without medicine_id working!")
            print(f"Selected Medicine: {data.get('medicine_name', 'N/A')}")
            print(f"Forecast Period: {data.get('forecast_period', 'N/A')}")
            print(f"Forecast Horizon: {data.get('forecast_horizon', 'N/A')}")
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception during API test: {str(e)}")
        return False
    
    # Test 2: API with specific medicine_id
    print("\n--- Test 2: API with specific medicine_id ---")
    medicines = Medicine.objects.filter(is_active=True)
    if medicines.exists():
        test_medicine = medicines.first()
        print(f"Testing with medicine: {test_medicine.name} (ID: {test_medicine.id})")
        
        try:
            response = client.get(f'/analytics/api/forecast/best-auto/?medicine_id={test_medicine.id}')
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Auto-forecast API with medicine_id working!")
                print(f"Selected Medicine: {data.get('medicine_name', 'N/A')}")
                print(f"Forecast Period: {data.get('forecast_period', 'N/A')}")
                print(f"Forecast Horizon: {data.get('forecast_horizon', 'N/A')}")
                print(f"Model Quality: {data.get('model_info', {}).get('model_quality', 'N/A')}")
                print(f"MAPE: {data.get('model_info', {}).get('mape', 'N/A')}%")
            else:
                print(f"❌ API Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error content: {response.content}")
                return False
        except Exception as e:
            print(f"❌ Exception during API test: {str(e)}")
            return False
    else:
        print("❌ No medicines found for testing")
        return False
    
    # Test 3: API with invalid medicine_id
    print("\n--- Test 3: API with invalid medicine_id ---")
    try:
        response = client.get('/analytics/api/forecast/best-auto/?medicine_id=99999')
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ API correctly handles invalid medicine_id")
        else:
            print(f"❌ Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception during API test: {str(e)}")
        return False
    
    return True

def check_medicines_data():
    """Check if there are medicines with sufficient data"""
    print("\nChecking medicines data...")
    
    medicines = Medicine.objects.filter(is_active=True)
    print(f"Total active medicines: {medicines.count()}")
    
    for medicine in medicines:
        print(f"- {medicine.name} (ID: {medicine.id})")
    
    # Check if there are any order items for these medicines
    from orders.models import OrderItem
    from django.db.models import Count
    
    medicine_counts = OrderItem.objects.values('medicine__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print(f"\nMedicine order counts:")
    for item in medicine_counts[:10]:  # Show top 10
        print(f"- {item['medicine__name']}: {item['count']} orders")
    
    return len(medicine_counts) > 0

if __name__ == "__main__":
    print("=" * 60)
    print("MODIFIED AUTO-FORECAST FLOW TEST")
    print("=" * 60)
    
    # Check medicines data first
    has_data = check_medicines_data()
    
    if not has_data:
        print("❌ No medicine data found. Please run data generation scripts first.")
        sys.exit(1)
    
    # Test the modified flow
    success = test_modified_flow()
    
    if success:
        print("\n✅ All tests passed! Modified auto-forecast flow is working.")
        print("\nFlow Summary:")
        print("1. User selects medicine from dropdown")
        print("2. System automatically generates best model forecast")
        print("3. Period and horizon dropdowns update to match best model")
        print("4. Chart displays with optimal settings")
    else:
        print("\n❌ Tests failed. Please check the implementation.")
    
    print("=" * 60)
