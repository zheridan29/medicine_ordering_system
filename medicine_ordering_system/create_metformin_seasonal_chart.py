#!/usr/bin/env python3
"""
Create seasonal pattern visualization for Metformin data
Based on the actual system data structure and patterns
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, date
import seaborn as sns

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from analytics.services import ARIMAForecastingService
from inventory.models import Medicine

def create_metformin_seasonal_chart():
    """Create seasonal pattern chart for Metformin data"""
    print("=== Creating Metformin Seasonal Pattern Chart ===")
    
    try:
        # Initialize forecasting service
        service = ARIMAForecastingService()
        
        # Get Metformin data (ID = 4)
        metformin = Medicine.objects.get(id=4)
        print(f"✅ Found medicine: {metformin.name}")
        
        # Prepare monthly data for seasonal analysis
        monthly_data = service.prepare_sales_data(4, 'monthly')
        
        if len(monthly_data) == 0:
            print("❌ No monthly data available for Metformin")
            return
        
        print(f"📊 Monthly data points: {len(monthly_data)}")
        print(f"📅 Date range: {monthly_data['date'].min()} to {monthly_data['date'].max()}")
        
        # Set up the plot style
        plt.style.use('seaborn-v0_8')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Chart 1: Monthly Time Series
        ax1.plot(monthly_data['date'], monthly_data['quantity'], 
                linewidth=2, color='#2E86AB', marker='o', markersize=4)
        ax1.set_title('Metformin 500mg - Monthly Sales Pattern (2015-2025)', 
                     fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Quantity Sold (Units)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis
        ax1.xaxis.set_major_locator(mdates.YearLocator())
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax1.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))
        
        # Add trend line
        z = np.polyfit(range(len(monthly_data)), monthly_data['quantity'], 1)
        p = np.poly1d(z)
        ax1.plot(monthly_data['date'], p(range(len(monthly_data))), 
                "r--", alpha=0.8, linewidth=2, label='Trend Line')
        ax1.legend()
        
        # Chart 2: Seasonal Decomposition
        # Create a proper time series for decomposition
        ts_data = monthly_data.set_index('date')['quantity']
        
        # Handle any missing values
        ts_data = ts_data.fillna(ts_data.mean())
        
        # Seasonal decomposition
        from statsmodels.tsa.seasonal import seasonal_decompose
        
        # Ensure we have enough data for decomposition
        if len(ts_data) >= 24:  # At least 2 years of monthly data
            decomposition = seasonal_decompose(ts_data, model='additive', period=12)
            
            # Plot decomposition components separately
            ax2.plot(ts_data.index, decomposition.trend, label='Trend', linewidth=2, color='blue')
            ax2.plot(ts_data.index, decomposition.seasonal, label='Seasonal', linewidth=2, color='red')
            ax2.plot(ts_data.index, decomposition.resid, label='Residual', linewidth=2, color='green')
            ax2.set_title('Metformin 500mg - Seasonal Decomposition', 
                         fontsize=16, fontweight='bold', pad=20)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            # If not enough data, show monthly averages by month
            monthly_data['month'] = monthly_data['date'].dt.month
            monthly_avg = monthly_data.groupby('month')['quantity'].mean()
            
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            ax2.bar(months, monthly_avg.values, color='#A23B72', alpha=0.7)
            ax2.set_title('Metformin 500mg - Average Monthly Sales by Month', 
                         fontsize=16, fontweight='bold', pad=20)
            ax2.set_xlabel('Month', fontsize=12)
            ax2.set_ylabel('Average Quantity Sold', fontsize=12)
            ax2.grid(True, alpha=0.3)
        
        # Add annotations for key patterns
        if len(monthly_data) > 0:
            max_quantity = monthly_data['quantity'].max()
            max_date = monthly_data.loc[monthly_data['quantity'].idxmax(), 'date']
            min_quantity = monthly_data['quantity'].min()
            min_date = monthly_data.loc[monthly_data['quantity'].idxmin(), 'date']
            
            # Annotate peak and trough
            ax1.annotate(f'Peak: {max_quantity:.0f} units\n{max_date.strftime("%Y-%m")}', 
                        xy=(max_date, max_quantity), xytext=(10, 10),
                        textcoords='offset points', bbox=dict(boxstyle='round,pad=0.5', 
                        fc='yellow', alpha=0.7), arrowprops=dict(arrowstyle='->', 
                        connectionstyle='arc3,rad=0'))
            
            ax1.annotate(f'Trough: {min_quantity:.0f} units\n{min_date.strftime("%Y-%m")}', 
                        xy=(min_date, min_quantity), xytext=(10, -20),
                        textcoords='offset points', bbox=dict(boxstyle='round,pad=0.5', 
                        fc='lightblue', alpha=0.7), arrowprops=dict(arrowstyle='->', 
                        connectionstyle='arc3,rad=0'))
        
        # Add statistics text box
        stats_text = f"""Data Statistics:
• Total Data Points: {len(monthly_data)}
• Date Range: {monthly_data['date'].min().strftime('%Y-%m')} to {monthly_data['date'].max().strftime('%Y-%m')}
• Mean Quantity: {monthly_data['quantity'].mean():.1f}
• Std Deviation: {monthly_data['quantity'].std():.1f}
• Min Quantity: {monthly_data['quantity'].min():.0f}
• Max Quantity: {monthly_data['quantity'].max():.0f}
• Growth Rate: {((monthly_data['quantity'].iloc[-1] / monthly_data['quantity'].iloc[0]) - 1) * 100:.1f}%"""
        
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, 
                fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', 
                facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        # Save the chart
        output_path = 'metformin_seasonal_patterns.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        print(f"✅ Chart saved as: {output_path}")
        
        # Also create a weekly pattern chart
        create_weekly_pattern_chart(service, metformin)
        
        plt.show()
        
    except Exception as e:
        print(f"❌ Error creating chart: {e}")
        import traceback
        traceback.print_exc()

def create_weekly_pattern_chart(service, metformin):
    """Create weekly pattern chart for additional analysis"""
    try:
        # Get weekly data
        weekly_data = service.prepare_sales_data(4, 'weekly')
        
        if len(weekly_data) == 0:
            print("❌ No weekly data available")
            return
        
        # Create weekly pattern chart
        fig, ax = plt.subplots(figsize=(15, 8))
        
        # Plot weekly data
        ax.plot(weekly_data['date'], weekly_data['quantity'], 
               linewidth=1.5, color='#F18F01', marker='o', markersize=3)
        
        ax.set_title(f'{metformin.name} - Weekly Sales Pattern', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Quantity Sold (Units)', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        
        # Add trend line
        z = np.polyfit(range(len(weekly_data)), weekly_data['quantity'], 1)
        p = np.poly1d(z)
        ax.plot(weekly_data['date'], p(range(len(weekly_data))), 
               "r--", alpha=0.8, linewidth=2, label='Trend Line')
        ax.legend()
        
        # Add statistics
        stats_text = f"""Weekly Data Statistics:
• Total Weeks: {len(weekly_data)}
• Mean Weekly Sales: {weekly_data['quantity'].mean():.1f}
• Std Deviation: {weekly_data['quantity'].std():.1f}
• Peak Week: {weekly_data['quantity'].max():.0f} units
• Low Week: {weekly_data['quantity'].min():.0f} units"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', 
               facecolor='lightgreen', alpha=0.8))
        
        plt.tight_layout()
        
        # Save weekly chart
        output_path = 'metformin_weekly_patterns.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        print(f"✅ Weekly chart saved as: {output_path}")
        
    except Exception as e:
        print(f"❌ Error creating weekly chart: {e}")

def create_seasonal_boxplot():
    """Create seasonal boxplot showing monthly patterns"""
    try:
        service = ARIMAForecastingService()
        monthly_data = service.prepare_sales_data(4, 'monthly')
        
        if len(monthly_data) == 0:
            return
        
        # Add month names
        monthly_data['month_name'] = monthly_data['date'].dt.month_name()
        monthly_data['month_num'] = monthly_data['date'].dt.month
        
        # Create boxplot
        plt.figure(figsize=(12, 8))
        
        # Order months properly
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        # Create boxplot
        sns.boxplot(data=monthly_data, x='month_name', y='quantity', 
                   order=month_order, palette='Set3')
        
        plt.title('Metformin 500mg - Seasonal Distribution by Month', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Quantity Sold (Units)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save boxplot
        output_path = 'metformin_seasonal_boxplot.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        
        print(f"✅ Seasonal boxplot saved as: {output_path}")
        
    except Exception as e:
        print(f"❌ Error creating boxplot: {e}")

if __name__ == "__main__":
    print("Creating Metformin seasonal pattern visualizations...")
    create_metformin_seasonal_chart()
    create_seasonal_boxplot()
    print("✅ All charts created successfully!")
