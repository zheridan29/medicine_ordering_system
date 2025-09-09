#!/usr/bin/env python3
"""
Create Combined Figure for STEP 1 (Stationarity Testing) and STEP 2 (Seasonal Decomposition)
ARIMA Demonstration for Metformin Data
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, date
import warnings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from analytics.services import ARIMAForecastingService
from inventory.models import Medicine
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import acf, pacf
import seaborn as sns

warnings.filterwarnings('ignore')

def create_combined_analysis_figure():
    """Create a comprehensive figure combining stationarity testing and seasonal decomposition"""
    print("=== Creating Combined Analysis Figure ===")
    print("STEP 1: Stationarity Testing + STEP 2: Seasonal Decomposition")
    
    try:
        # Initialize forecasting service
        service = ARIMAForecastingService()
        
        # Get Metformin data
        metformin = Medicine.objects.get(id=4)
        print(f"✅ Medicine: {metformin.name}")
        
        # Prepare monthly data
        monthly_data = service.prepare_sales_data(4, 'monthly')
        
        if len(monthly_data) == 0:
            print("❌ No monthly data available")
            return
        
        print(f"📊 Data Points: {len(monthly_data)}")
        print(f"📅 Date Range: {monthly_data['date'].min()} to {monthly_data['date'].max()}")
        
        # Prepare time series data
        ts_data = monthly_data.set_index('date')['quantity']
        ts_data = ts_data.fillna(ts_data.mean())
        
        # Create the combined figure
        fig = plt.figure(figsize=(24, 20))
        
        # Set up the grid layout with more spacing
        gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1, 1.2], width_ratios=[1, 1, 1], 
                             hspace=0.4, wspace=0.4)
        
        # STEP 1: STATIONARITY TESTING
        # 1.1: Original Time Series
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='#2E86AB', marker='o', markersize=2)
        ax1.set_title('STEP 1.1: Original Time Series\nMetformin 500mg Sales Data', 
                     fontsize=11, fontweight='bold', pad=15)
        ax1.set_xlabel('Date', fontsize=10)
        ax1.set_ylabel('Quantity Sold', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45, labelsize=8)
        ax1.tick_params(axis='y', labelsize=8)
        
        # Add trend line
        z = np.polyfit(range(len(ts_data)), ts_data.values, 1)
        p = np.poly1d(z)
        ax1.plot(ts_data.index, p(range(len(ts_data))), "r--", alpha=0.8, linewidth=2, label='Trend Line')
        ax1.legend(fontsize=9)
        
        # 1.2: ADF Test Results
        ax2 = fig.add_subplot(gs[0, 1])
        adf_result = adfuller(ts_data.dropna())
        
        # Create ADF test visualization
        ax2.axis('off')
        ax2.text(0.05, 0.95, 'STEP 1.2: Augmented Dickey-Fuller Test', 
                fontsize=11, fontweight='bold', transform=ax2.transAxes)
        
        ax2.text(0.05, 0.85, f'ADF Statistic: {adf_result[0]:.6f}', 
                fontsize=9, transform=ax2.transAxes)
        ax2.text(0.05, 0.8, f'p-value: {adf_result[1]:.6f}', 
                fontsize=9, transform=ax2.transAxes)
        ax2.text(0.05, 0.75, f'Critical Values:', 
                fontsize=9, fontweight='bold', transform=ax2.transAxes)
        
        y_pos = 0.7
        for key, value in adf_result[4].items():
            ax2.text(0.1, y_pos, f'  {key}: {value:.6f}', 
                    fontsize=8, transform=ax2.transAxes)
            y_pos -= 0.04
        
        # Stationarity conclusion
        is_stationary = adf_result[1] <= 0.05
        conclusion = "STATIONARY" if is_stationary else "NON-STATIONARY"
        color = "green" if is_stationary else "red"
        
        ax2.text(0.05, 0.45, f'Conclusion: {conclusion}', 
                fontsize=10, fontweight='bold', color=color, transform=ax2.transAxes)
        ax2.text(0.05, 0.4, f'{"p-value ≤ 0.05" if is_stationary else "p-value > 0.05"}', 
                fontsize=9, transform=ax2.transAxes)
        
        # 1.3: Data Statistics
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.axis('off')
        ax3.text(0.05, 0.95, 'STEP 1.3: Data Statistics', 
                fontsize=11, fontweight='bold', transform=ax3.transAxes)
        
        stats_text = f"""Mean: {ts_data.mean():.2f}
Std Dev: {ts_data.std():.2f}
Min: {ts_data.min():.2f}
Max: {ts_data.max():.2f}
Range: {ts_data.max() - ts_data.min():.2f}
Skewness: {ts_data.skew():.3f}
Kurtosis: {ts_data.kurtosis():.3f}"""
        
        ax3.text(0.05, 0.75, stats_text, fontsize=9, transform=ax3.transAxes, 
                verticalalignment='top', fontfamily='monospace')
        
        # STEP 2: SEASONAL DECOMPOSITION
        # 2.1: Original Data (for reference)
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.plot(ts_data.index, ts_data.values, linewidth=2, color='blue', label='Original')
        ax4.set_title('STEP 2.1: Original Data\n(Reference for Decomposition)', 
                     fontsize=11, fontweight='bold', pad=15)
        ax4.set_xlabel('Date', fontsize=10)
        ax4.set_ylabel('Quantity Sold', fontsize=10)
        ax4.legend(fontsize=9)
        ax4.grid(True, alpha=0.3)
        ax4.tick_params(axis='x', rotation=45, labelsize=8)
        ax4.tick_params(axis='y', labelsize=8)
        
        # 2.2: Seasonal Decomposition
        if len(ts_data) >= 24:
            decomposition = seasonal_decompose(ts_data, model='additive', period=12)
            
            # Trend Component
            ax5 = fig.add_subplot(gs[1, 1])
            ax5.plot(ts_data.index, decomposition.trend, linewidth=2, color='red', label='Trend')
            ax5.set_title('STEP 2.2: Trend Component\n(Decomposed from Original)', 
                         fontsize=11, fontweight='bold', pad=15)
            ax5.set_xlabel('Date', fontsize=10)
            ax5.set_ylabel('Trend Value', fontsize=10)
            ax5.legend(fontsize=9)
            ax5.grid(True, alpha=0.3)
            ax5.tick_params(axis='x', rotation=45, labelsize=8)
            ax5.tick_params(axis='y', labelsize=8)
            
            # Seasonal Component
            ax6 = fig.add_subplot(gs[1, 2])
            ax6.plot(ts_data.index, decomposition.seasonal, linewidth=2, color='green', label='Seasonal')
            ax6.set_title('STEP 2.3: Seasonal Component\n(12-Month Pattern)', 
                         fontsize=11, fontweight='bold', pad=15)
            ax6.set_xlabel('Date', fontsize=10)
            ax6.set_ylabel('Seasonal Value', fontsize=10)
            ax6.legend(fontsize=9)
            ax6.grid(True, alpha=0.3)
            ax6.tick_params(axis='x', rotation=45, labelsize=8)
            ax6.tick_params(axis='y', labelsize=8)
            
            # Residual Component
            ax7 = fig.add_subplot(gs[2, 0])
            ax7.plot(ts_data.index, decomposition.resid, linewidth=2, color='orange', label='Residual')
            ax7.set_title('STEP 2.4: Residual Component\n(Noise/Error)', 
                         fontsize=11, fontweight='bold', pad=15)
            ax7.set_xlabel('Date', fontsize=10)
            ax7.set_ylabel('Residual Value', fontsize=10)
            ax7.legend(fontsize=9)
            ax7.grid(True, alpha=0.3)
            ax7.tick_params(axis='x', rotation=45, labelsize=8)
            ax7.tick_params(axis='y', labelsize=8)
            
            # Seasonal Analysis Summary
            ax8 = fig.add_subplot(gs[2, 1])
            ax8.axis('off')
            ax8.text(0.05, 0.95, 'STEP 2.5: Seasonal Analysis', 
                    fontsize=11, fontweight='bold', transform=ax8.transAxes)
            
            seasonal_strength = np.var(decomposition.seasonal) / np.var(ts_data)
            trend_strength = np.var(decomposition.trend) / np.var(ts_data)
            residual_strength = np.var(decomposition.resid) / np.var(ts_data)
            
            analysis_text = f"""Components Present:
• Trend: {'Yes' if decomposition.trend.notna().any() else 'No'}
• Seasonal: {'Yes' if decomposition.seasonal.notna().any() else 'No'}
• Residual: {'Yes' if decomposition.resid.notna().any() else 'No'}

Component Strengths:
• Seasonal: {seasonal_strength:.4f}
• Trend: {trend_strength:.4f}
• Residual: {residual_strength:.4f}

Seasonal Assessment:
{'STRONG' if seasonal_strength > 0.1 else 'WEAK'} Seasonal Pattern
Seasonal Strength: {seasonal_strength:.1%}"""
            
            ax8.text(0.05, 0.7, analysis_text, fontsize=9, transform=ax8.transAxes, 
                    verticalalignment='top')
            
            # Monthly Pattern Analysis
            ax9 = fig.add_subplot(gs[2, 2])
            monthly_avg = ts_data.groupby(ts_data.index.month).mean()
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            bars = ax9.bar(months, monthly_avg.values, color='skyblue', alpha=0.7, edgecolor='navy')
            ax9.set_title('STEP 2.6: Monthly Pattern\n(Average Sales by Month)', 
                         fontsize=11, fontweight='bold', pad=15)
            ax9.set_xlabel('Month', fontsize=10)
            ax9.set_ylabel('Average Quantity', fontsize=10)
            ax9.grid(True, alpha=0.3)
            ax9.tick_params(axis='x', rotation=45, labelsize=8)
            ax9.tick_params(axis='y', labelsize=8)
            
            # Highlight peak and trough months
            max_month = monthly_avg.idxmax()
            min_month = monthly_avg.idxmin()
            bars[max_month-1].set_color('red')
            bars[min_month-1].set_color('green')
            
            # Add annotations with better positioning
            ax9.annotate(f'Peak: {months[max_month-1]}', 
                        xy=(max_month-1, monthly_avg.max()), 
                        xytext=(max_month-1, monthly_avg.max() + monthly_avg.max() * 0.05),
                        ha='center', fontweight='bold', color='red', fontsize=8)
            ax9.annotate(f'Trough: {months[min_month-1]}', 
                        xy=(min_month-1, monthly_avg.min()), 
                        xytext=(min_month-1, monthly_avg.min() - monthly_avg.max() * 0.05),
                        ha='center', fontweight='bold', color='green', fontsize=8)
        
        # Combined Analysis Summary
        ax10 = fig.add_subplot(gs[3, :])
        ax10.axis('off')
        
        # Create summary text with better formatting
        summary_text = f"""COMBINED ANALYSIS SUMMARY - Metformin 500mg Sales Data
{'='*70}

STEP 1: STATIONARITY TESTING
• ADF Test Result: {conclusion} (p-value: {adf_result[1]:.6f})
• Data Characteristics: {'Stationary data suitable for ARIMA modeling' if is_stationary else 'Non-stationary data requiring differencing'}
• Statistical Properties: Mean={ts_data.mean():.1f}, Std={ts_data.std():.1f}, Range={ts_data.max()-ts_data.min():.1f}

STEP 2: SEASONAL DECOMPOSITION
• Seasonal Pattern: {'STRONG' if 'seasonal_strength' in locals() and seasonal_strength > 0.1 else 'WEAK'} (Strength: {seasonal_strength:.1%} if 'seasonal_strength' in locals() else 'N/A')
• Trend Component: {'Present' if 'decomposition' in locals() and decomposition.trend.notna().any() else 'Not detected'}
• Seasonal Component: {'Present' if 'decomposition' in locals() and decomposition.seasonal.notna().any() else 'Not detected'}
• Peak Month: {months[max_month-1] if 'max_month' in locals() else 'N/A'} | Trough Month: {months[min_month-1] if 'min_month' in locals() else 'N/A'}

CONCLUSION: The data exhibits {'both stationarity and strong seasonal patterns' if is_stationary and 'seasonal_strength' in locals() and seasonal_strength > 0.1 else 'stationarity with weak seasonal patterns' if is_stationary else 'non-stationarity requiring preprocessing'}, 
making it suitable for {'seasonal ARIMA (SARIMA) modeling' if 'seasonal_strength' in locals() and seasonal_strength > 0.1 else 'standard ARIMA modeling' if is_stationary else 'ARIMA modeling with differencing'}."""
        
        ax10.text(0.02, 0.95, summary_text, fontsize=10, transform=ax10.transAxes, 
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        # Add main title
        fig.suptitle('ARIMA DEMONSTRATION: STEP 1 & STEP 2 COMBINED ANALYSIS\n' + 
                    'Stationarity Testing + Seasonal Decomposition for Metformin 500mg', 
                    fontsize=16, fontweight='bold', y=0.98)
        
        # Save the figure
        output_path = 'metformin_combined_analysis_steps_1_2.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"✅ Combined figure saved as: {output_path}")
        
        # Also create a PDF version
        output_path_pdf = 'metformin_combined_analysis_steps_1_2.pdf'
        plt.savefig(output_path_pdf, format='pdf', bbox_inches='tight', facecolor='white', edgecolor='none')
        print(f"✅ PDF version saved as: {output_path_pdf}")
        
        plt.show()
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating combined figure: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Creating combined analysis figure for Steps 1 & 2...")
    result = create_combined_analysis_figure()
    if result:
        print(f"🎉 Successfully created: {result}")
    else:
        print("❌ Failed to create combined figure")
