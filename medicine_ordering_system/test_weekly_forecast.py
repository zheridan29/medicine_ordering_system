#!/usr/bin/env python
"""
Test script for weekly forecast to debug the datetime issue
"""

import os
import sys
import django
from datetime import datetime, date, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from analytics.services import ARIMAForecastingService
from inventory.models import Medicine

def test_weekly_forecast():
    """Test weekly forecast generation"""
    print("=== TESTING WEEKLY FORECAST ===")
    
    try:
        # Get Paracetamol medicine
        paracetamol = Medicine.objects.get(name='Paracetamol')
        print(f"✅ Found medicine: {paracetamol.name}")
        
        # Initialize forecasting service
        service = ARIMAForecastingService()
        
        # Test data preparation
        print("Testing data preparation...")
        sales_data = service.prepare_sales_data(paracetamol.id, 'weekly')
        print(f"✅ Data prepared successfully")
        print(f"   Records: {len(sales_data)}")
        print(f"   Columns: {sales_data.columns.tolist()}")
        print(f"   Date range: {sales_data['date'].min()} to {sales_data['date'].max()}")
        print(f"   Sample data:")
        print(sales_data.head())
        
        # Test forecast generation
        print("\nTesting forecast generation...")
        forecast = service.generate_forecast(paracetamol.id, 'weekly', 4)
        print(f"✅ Forecast generated successfully")
        print(f"   Forecast ID: {forecast.id}")
        print(f"   ARIMA params: ({forecast.arima_p}, {forecast.arima_d}, {forecast.arima_q})")
        print(f"   Forecast values: {forecast.forecasted_demand}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_weekly_forecast()
