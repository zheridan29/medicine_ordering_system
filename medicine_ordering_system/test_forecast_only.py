#!/usr/bin/env python3
"""
Test script to verify Forecast-Only View data
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from analytics.models import DemandForecast
from inventory.models import Medicine
from analytics.services import ARIMAForecastingService

def test_forecast_only_data():
    print("=== Testing Forecast-Only View Data ===")
    
    # Check if we have forecasts
    forecasts = DemandForecast.objects.filter(is_active=True)
    print(f"Total active forecasts: {forecasts.count()}")
    
    if forecasts.exists():
        # Check medicines with forecasts
        medicine_ids = set(forecasts.values_list('medicine_id', flat=True))
        print(f"Medicines with forecasts: {medicine_ids}")
        
        for medicine_id in medicine_ids:
            medicine = Medicine.objects.get(id=medicine_id)
            medicine_forecasts = forecasts.filter(medicine_id=medicine_id)
            best_forecast = medicine_forecasts.order_by('aic').first()
            
            print(f"\nMedicine: {medicine.name} (ID: {medicine_id})")
            print(f"  Total forecasts: {medicine_forecasts.count()}")
            print(f"  Best forecast AIC: {best_forecast.aic if best_forecast else 'N/A'}")
            print(f"  Best forecast MAPE: {best_forecast.mape if best_forecast else 'N/A'}")
            
            # Test data preparation
            if best_forecast:
                try:
                    service = ARIMAForecastingService()
                    data = service.prepare_sales_data(medicine_id, best_forecast.forecast_period)
                    print(f"  Historical data points: {len(data)}")
                    print(f"  Data range: {data['date'].min()} to {data['date'].max()}")
                    print(f"  Quantity range: {data['quantity'].min()} to {data['quantity'].max()}")
                except Exception as e:
                    print(f"  Error preparing data: {e}")
    else:
        print("No forecasts found!")
    
    # Check specific medicines
    print(f"\n=== Medicine Inventory ===")
    medicines = Medicine.objects.all().order_by('name')
    for medicine in medicines:
        print(f"{medicine.name} (ID: {medicine.id}) - Stock: {medicine.current_stock}")

if __name__ == "__main__":
    test_forecast_only_data()
