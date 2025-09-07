#!/usr/bin/env python
"""
Verify Paracetamol time series data quality
"""

import os
import sys
import django
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from inventory.models import Medicine
from orders.models import Order, OrderItem
from analytics.models import SalesTrend, DemandForecast

def main():
    # Get Paracetamol medicine
    paracetamol = Medicine.objects.get(name='Paracetamol')
    print('=== PARACETAMOL TIME SERIES DATA SUMMARY ===')
    print(f'Medicine: {paracetamol.name} ({paracetamol.strength})')
    print(f'NDC Number: {paracetamol.ndc_number}')
    print(f'Unit Price: ${paracetamol.unit_price}')
    print(f'Current Stock: {paracetamol.current_stock} units')
    print()

    # Count orders for Paracetamol
    paracetamol_orders = Order.objects.filter(items__medicine=paracetamol).distinct()
    print(f'Total Orders with Paracetamol: {paracetamol_orders.count()}')

    # Get date range
    first_order = paracetamol_orders.order_by('created_at').first()
    last_order = paracetamol_orders.order_by('created_at').last()
    print(f'Date Range: {first_order.created_at.date()} to {last_order.created_at.date()}')
    print()

    # Count order items
    total_items = OrderItem.objects.filter(medicine=paracetamol).count()
    total_quantity = sum(item.quantity for item in OrderItem.objects.filter(medicine=paracetamol))
    total_revenue = sum(float(item.total_price) for item in OrderItem.objects.filter(medicine=paracetamol))
    
    print(f'Total Order Items: {total_items}')
    print(f'Total Quantity Sold: {total_quantity} units')
    print(f'Total Revenue: ${total_revenue:.2f}')
    print()

    # Check data quality
    print('=== DATA QUALITY VERIFICATION ===')
    
    # Check for gaps in data
    order_dates = [order.created_at.date() for order in paracetamol_orders.order_by('created_at')]
    unique_dates = sorted(set(order_dates))
    
    print(f'Days with sales data: {len(unique_dates)}')
    print(f'First sale date: {min(unique_dates)}')
    print(f'Last sale date: {max(unique_dates)}')
    
    # Check for major gaps (more than 7 days without sales)
    gaps = []
    for i in range(len(unique_dates) - 1):
        gap_days = (unique_dates[i+1] - unique_dates[i]).days
        if gap_days > 7:
            gaps.append((unique_dates[i], unique_dates[i+1], gap_days))
    
    if gaps:
        print(f'⚠️  Found {len(gaps)} gaps longer than 7 days:')
        for start, end, days in gaps:
            print(f'   Gap: {start} to {end} ({days} days)')
    else:
        print('✅ No major gaps found in sales data')
    
    print()

    # Check analytics data
    print('=== ANALYTICS DATA VERIFICATION ===')
    
    sales_trends = SalesTrend.objects.filter(medicine=paracetamol)
    print(f'Sales Trend Records: {sales_trends.count()}')
    
    demand_forecasts = DemandForecast.objects.filter(medicine=paracetamol)
    print(f'Demand Forecast Records: {demand_forecasts.count()}')
    
    if sales_trends.exists():
        print('Monthly Sales Trends:')
        for trend in sales_trends.order_by('period'):
            print(f'  {trend.period}: {trend.total_quantity_sold} units, ${trend.total_revenue:.2f} revenue')
    
    print()

    # Check forecasting requirements
    print('=== FORECASTING REQUIREMENTS CHECK ===')
    
    # Minimum 30 sales records
    min_records = 30
    actual_records = paracetamol_orders.count()
    print(f'Minimum 30 sales records: {actual_records} >= {min_records} = {"✅ PASS" if actual_records >= min_records else "❌ FAIL"}')
    
    # 6+ months of data
    min_months = 6
    date_range = (max(unique_dates) - min(unique_dates)).days
    actual_months = date_range / 30.44  # Average days per month
    print(f'6+ months of data: {actual_months:.1f} months >= {min_months} = {"✅ PASS" if actual_months >= min_months else "❌ FAIL"}')
    
    # Consistent data without major gaps
    consistent_data = len(gaps) == 0
    print(f'Consistent data without major gaps: {"✅ PASS" if consistent_data else "❌ FAIL"}')
    
    # Full seasonal cycles
    months_with_data = len(set(date.month for date in unique_dates))
    seasonal_cycles = months_with_data >= 12
    print(f'Full seasonal cycles: {months_with_data} months >= 12 = {"✅ PASS" if seasonal_cycles else "❌ FAIL"}')
    
    # Data from 2020
    data_from_2020 = min(unique_dates).year == 2020
    print(f'Data from 2020: {min(unique_dates).year} == 2020 = {"✅ PASS" if data_from_2020 else "❌ FAIL"}')
    
    print()
    
    # Overall assessment
    all_requirements_met = (
        actual_records >= min_records and
        actual_months >= min_months and
        consistent_data and
        seasonal_cycles and
        data_from_2020
    )
    
    print('=== OVERALL ASSESSMENT ===')
    if all_requirements_met:
        print('🎉 ALL FORECASTING REQUIREMENTS MET!')
        print('✅ Data is ready for ARIMA-based demand forecasting')
    else:
        print('⚠️  Some requirements not met. Check the details above.')
    
    print()
    print('=== SUMMARY STATISTICS ===')
    print(f'Total Orders: {actual_records}')
    print(f'Total Quantity: {total_quantity} units')
    print(f'Total Revenue: ${total_revenue:.2f}')
    print(f'Average Order Value: ${total_revenue/actual_records:.2f}')
    print(f'Average Quantity per Order: {total_quantity/actual_records:.1f} units')
    print(f'Data Span: {date_range} days ({actual_months:.1f} months)')
    print(f'Unique Sales Days: {len(unique_dates)}')

if __name__ == "__main__":
    main()
