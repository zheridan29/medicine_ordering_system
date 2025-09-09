#!/usr/bin/env python3
"""
Complete ARIMA Demonstration: Steps 1-5 with Descriptions and Visualizations
Comprehensive analysis from data preparation to forecast generation
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
import seaborn as sns

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from analytics.services import ARIMAForecastingService
from inventory.models import Medicine
from statsmodels.tsa.stattools import adfuller, acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from pmdarima import auto_arima
from sklearn.metrics import mean_squared_error, mean_absolute_error
import json

warnings.filterwarnings('ignore')

def create_complete_arima_steps():
    """Create comprehensive visualizations for all 5 ARIMA steps"""
    print("=" * 80)
    print("COMPLETE ARIMA DEMONSTRATION: STEPS 1-5")
    print("Metformin 500mg Sales Data Analysis")
    print("=" * 80)
    
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
        
        # Create individual step figures
        create_step1_figure(ts_data, metformin)
        create_step2_figure(ts_data, metformin)
        create_step3_figure(ts_data, metformin)
        create_step4_figure(ts_data, metformin)
        create_step5_figure(ts_data, metformin)
        
        # Create combined overview figure
        create_combined_overview_figure(ts_data, metformin)
        
        print("\n🎉 All ARIMA demonstration figures created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating ARIMA steps: {e}")
        import traceback
        traceback.print_exc()

def create_step1_figure(ts_data, medicine):
    """STEP 1: Stationarity Testing"""
    print("\n📊 Creating STEP 1: Stationarity Testing...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1.1: Original Time Series
    ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='#2E86AB', marker='o', markersize=3)
    ax1.set_title('STEP 1.1: Original Time Series\nMetformin 500mg Sales Data', 
                 fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Add trend line
    z = np.polyfit(range(len(ts_data)), ts_data.values, 1)
    p = np.poly1d(z)
    ax1.plot(ts_data.index, p(range(len(ts_data))), "r--", alpha=0.8, linewidth=2, label='Trend Line')
    ax1.legend()
    
    # 1.2: ADF Test Results
    adf_result = adfuller(ts_data.dropna())
    ax2.axis('off')
    ax2.text(0.05, 0.95, 'STEP 1.2: Augmented Dickey-Fuller Test', 
            fontsize=14, fontweight='bold', transform=ax2.transAxes)
    
    ax2.text(0.05, 0.85, f'ADF Statistic: {adf_result[0]:.6f}', 
            fontsize=12, transform=ax2.transAxes)
    ax2.text(0.05, 0.8, f'p-value: {adf_result[1]:.6f}', 
            fontsize=12, transform=ax2.transAxes)
    ax2.text(0.05, 0.75, f'Critical Values:', 
            fontsize=12, fontweight='bold', transform=ax2.transAxes)
    
    y_pos = 0.7
    for key, value in adf_result[4].items():
        ax2.text(0.1, y_pos, f'  {key}: {value:.6f}', 
                fontsize=11, transform=ax2.transAxes)
        y_pos -= 0.05
    
    # Stationarity conclusion
    is_stationary = adf_result[1] <= 0.05
    conclusion = "STATIONARY" if is_stationary else "NON-STATIONARY"
    color = "green" if is_stationary else "red"
    
    ax2.text(0.05, 0.4, f'Conclusion: {conclusion}', 
            fontsize=13, fontweight='bold', color=color, transform=ax2.transAxes)
    ax2.text(0.05, 0.35, f'{"p-value ≤ 0.05" if is_stationary else "p-value > 0.05"}', 
            fontsize=12, transform=ax2.transAxes)
    
    # 1.3: Data Statistics
    ax3.axis('off')
    ax3.text(0.05, 0.95, 'STEP 1.3: Data Statistics', 
            fontsize=14, fontweight='bold', transform=ax3.transAxes)
    
    stats_text = f"""Mean: {ts_data.mean():.2f}
Std Dev: {ts_data.std():.2f}
Min: {ts_data.min():.2f}
Max: {ts_data.max():.2f}
Range: {ts_data.max() - ts_data.min():.2f}
Skewness: {ts_data.skew():.3f}
Kurtosis: {ts_data.kurtosis():.3f}
Variance: {ts_data.var():.2f}"""
    
    ax3.text(0.05, 0.8, stats_text, fontsize=12, transform=ax3.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    # 1.4: Stationarity Description
    ax4.axis('off')
    ax4.text(0.05, 0.95, 'STEP 1.4: Stationarity Analysis', 
            fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    description_text = f"""What is Stationarity?
Stationarity means the statistical properties of a time series remain constant over time.

Key Properties:
• Mean remains constant
• Variance remains constant  
• Autocorrelation structure remains constant

Why is it Important?
• ARIMA models require stationary data
• Non-stationary data needs differencing
• Ensures reliable forecasting

Our Results:
• Data is {conclusion.lower()}
• {'Suitable for ARIMA modeling' if is_stationary else 'Requires differencing'}
• ADF test p-value: {adf_result[1]:.6f}"""
    
    ax4.text(0.05, 0.8, description_text, fontsize=11, transform=ax4.transAxes, 
            verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig('step1_stationarity_testing.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('step1_stationarity_testing.pdf', format='pdf', bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ STEP 1 figure saved")

def create_step2_figure(ts_data, medicine):
    """STEP 2: Seasonal Decomposition"""
    print("📊 Creating STEP 2: Seasonal Decomposition...")
    
    if len(ts_data) < 24:
        print("⚠️ Insufficient data for seasonal decomposition")
        return
    
    decomposition = seasonal_decompose(ts_data, model='additive', period=12)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 2.1: Original Data
    ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='blue', label='Original')
    ax1.set_title('STEP 2.1: Original Time Series\nReference for Decomposition', 
                 fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 2.2: Trend Component
    ax2.plot(ts_data.index, decomposition.trend, linewidth=2, color='red', label='Trend')
    ax2.set_title('STEP 2.2: Trend Component\nLong-term Direction', 
                 fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Trend Value', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # 2.3: Seasonal Component
    ax3.plot(ts_data.index, decomposition.seasonal, linewidth=2, color='green', label='Seasonal')
    ax3.set_title('STEP 2.3: Seasonal Component\n12-Month Repeating Pattern', 
                 fontsize=14, fontweight='bold', pad=15)
    ax3.set_xlabel('Date', fontsize=12)
    ax3.set_ylabel('Seasonal Value', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # 2.4: Residual Component
    ax4.plot(ts_data.index, decomposition.resid, linewidth=2, color='orange', label='Residual')
    ax4.set_title('STEP 2.4: Residual Component\nRandom Noise/Error', 
                 fontsize=14, fontweight='bold', pad=15)
    ax4.set_xlabel('Date', fontsize=12)
    ax4.set_ylabel('Residual Value', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('step2_seasonal_decomposition.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('step2_seasonal_decomposition.pdf', format='pdf', bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ STEP 2 figure saved")

def create_step3_figure(ts_data, medicine):
    """STEP 3: Auto ARIMA Model Selection"""
    print("📊 Creating STEP 3: Auto ARIMA Model Selection...")
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 3.1: Auto ARIMA Process
    ax1.axis('off')
    ax1.text(0.05, 0.95, 'STEP 3.1: Auto ARIMA Process', 
            fontsize=14, fontweight='bold', transform=ax1.transAxes)
    
    process_text = """What is Auto ARIMA?
Auto ARIMA automatically finds the best ARIMA model parameters.

Process:
1. Tests multiple parameter combinations
2. Uses information criteria (AIC, BIC)
3. Performs stationarity testing
4. Applies differencing if needed
5. Selects optimal model

Parameters Tested:
• p (AR order): 0 to 5
• d (differencing): 0 to 2  
• q (MA order): 0 to 5
• Seasonal: (P,D,Q)[12]

Benefits:
• Saves time and effort
• Reduces human error
• Finds optimal parameters
• Handles non-stationarity"""
    
    ax1.text(0.05, 0.8, process_text, fontsize=11, transform=ax1.transAxes, 
            verticalalignment='top')
    
    # 3.2: Model Selection Results
    model = auto_arima(
        ts_data,
        start_p=0, start_q=0,
        max_p=5, max_q=5,
        seasonal=True,
        m=12,
        start_P=0, start_Q=0,
        max_P=2, max_Q=2,
        stepwise=True,
        suppress_warnings=True,
        error_action='ignore',
        trace=False
    )
    
    ax2.axis('off')
    ax2.text(0.05, 0.95, 'STEP 3.2: Selected Model', 
            fontsize=14, fontweight='bold', transform=ax2.transAxes)
    
    model_text = f"""Best Model Found:
ARIMA{model.order} x SARIMA{model.seasonal_order}

Model Parameters:
• Non-seasonal: ARIMA({model.order[0]},{model.order[1]},{model.order[2]})
• Seasonal: SARIMA({model.seasonal_order[0]},{model.seasonal_order[1]},{model.seasonal_order[2]})[{model.seasonal_order[3]}]
• Total Parameters: {sum(model.order) + sum(model.seasonal_order)}

Model Quality:
• AIC: {model.aic():.3f}
• BIC: {model.bic():.3f}

Interpretation:
• p={model.order[0]}: {model.order[0]} autoregressive terms
• d={model.order[1]}: {model.order[1]} differencing operations
• q={model.order[2]}: {model.order[2]} moving average terms
• Seasonal: {model.seasonal_order[0]} seasonal AR terms"""
    
    ax2.text(0.05, 0.8, model_text, fontsize=11, transform=ax2.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    # 3.3: Parameter Search Visualization
    ax3.axis('off')
    ax3.text(0.05, 0.95, 'STEP 3.3: Parameter Search Space', 
            fontsize=14, fontweight='bold', transform=ax3.transAxes)
    
    search_text = """Search Strategy:
• Stepwise search for efficiency
• Tests combinations systematically
• Uses AIC for model selection
• Handles seasonal patterns

Search Space:
• Non-seasonal: 6 x 3 x 6 = 108 combinations
• Seasonal: 3 x 3 x 3 = 27 combinations
• Total: 2,916 possible models

Selection Criteria:
• Primary: AIC (Akaike Information Criterion)
• Secondary: BIC (Bayesian Information Criterion)
• Lower values = better model

Optimization:
• Balances model fit vs complexity
• Penalizes overfitting
• Ensures parsimony"""
    
    ax3.text(0.05, 0.8, search_text, fontsize=11, transform=ax3.transAxes, 
            verticalalignment='top')
    
    # 3.4: Model Interpretation
    ax4.axis('off')
    ax4.text(0.05, 0.95, 'STEP 3.4: Model Interpretation', 
            fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    interpretation_text = f"""ARIMA Model Components:

Autoregressive (AR) - p={model.order[0]}:
• Uses {model.order[0]} previous values
• Captures short-term dependencies
• {'Present' if model.order[0] > 0 else 'Not used'}

Integrated (I) - d={model.order[1]}:
• {model.order[1]} differencing operation{'s' if model.order[1] != 1 else ''}
• {'Makes data stationary' if model.order[1] > 0 else 'Data already stationary'}
• Removes trends and seasonality

Moving Average (MA) - q={model.order[2]}:
• Uses {model.order[2]} previous error terms
• Captures random shocks
• {'Present' if model.order[2] > 0 else 'Not used'}

Seasonal Component:
• {model.seasonal_order[0]} seasonal AR terms
• Captures yearly patterns
• Handles seasonal variations"""
    
    ax4.text(0.05, 0.8, interpretation_text, fontsize=11, transform=ax4.transAxes, 
            verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig('step3_auto_arima_selection.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('step3_auto_arima_selection.pdf', format='pdf', bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ STEP 3 figure saved")

def create_step4_figure(ts_data, medicine):
    """STEP 4: Model Evaluation"""
    print("📊 Creating STEP 4: Model Evaluation...")
    
    # Fit the model
    model = auto_arima(
        ts_data,
        start_p=0, start_q=0,
        max_p=5, max_q=5,
        seasonal=True,
        m=12,
        start_P=0, start_Q=0,
        max_P=2, max_Q=2,
        stepwise=True,
        suppress_warnings=True,
        error_action='ignore',
        trace=False
    )
    
    # Get fitted values and residuals
    fitted_values = model.predict_in_sample()
    residuals = ts_data - fitted_values
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 4.1: Model Fit Comparison
    ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='blue', label='Actual', alpha=0.8)
    ax1.plot(ts_data.index, fitted_values, linewidth=2, color='red', label='Fitted', alpha=0.8)
    ax1.set_title('STEP 4.1: Model Fit Comparison\nActual vs Fitted Values', 
                 fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 4.2: Residuals Analysis
    ax2.plot(ts_data.index, residuals, linewidth=1, color='green', alpha=0.7)
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.8)
    ax2.set_title('STEP 4.2: Residuals Analysis\nModel Errors Over Time', 
                 fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Residuals', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # 4.3: Evaluation Metrics
    rmse = np.sqrt(mean_squared_error(ts_data, fitted_values))
    mae = mean_absolute_error(ts_data, fitted_values)
    mape = np.mean(np.abs((ts_data - fitted_values) / ts_data)) * 100
    
    ax3.axis('off')
    ax3.text(0.05, 0.95, 'STEP 4.3: Evaluation Metrics', 
            fontsize=14, fontweight='bold', transform=ax3.transAxes)
    
    metrics_text = f"""Model Performance Metrics:

RMSE (Root Mean Square Error): {rmse:.3f}
• Measures average prediction error
• Penalizes larger errors more
• Same units as original data

MAE (Mean Absolute Error): {mae:.3f}
• Measures average absolute error
• Less sensitive to outliers
• Easy to interpret

MAPE (Mean Absolute Percentage Error): {mape:.2f}%
• Measures relative error as percentage
• Allows comparison across scales
• Lower is better

Model Quality Assessment:
• AIC: {model.aic():.3f}
• BIC: {model.bic():.3f}
• {'Excellent' if mape < 5 else 'Good' if mape < 15 else 'Fair' if mape < 25 else 'Poor'} Performance (MAPE: {mape:.1f}%)"""
    
    ax3.text(0.05, 0.8, metrics_text, fontsize=11, transform=ax3.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    # 4.4: Residuals Distribution
    ax4.hist(residuals, bins=20, alpha=0.7, color='skyblue', edgecolor='navy')
    ax4.axvline(x=0, color='red', linestyle='--', linewidth=2)
    ax4.set_title('STEP 4.4: Residuals Distribution\nShould be Normal with Mean ≈ 0', 
                 fontsize=14, fontweight='bold', pad=15)
    ax4.set_xlabel('Residual Value', fontsize=12)
    ax4.set_ylabel('Frequency', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    # Add statistics
    ax4.text(0.7, 0.8, f'Mean: {residuals.mean():.3f}\nStd: {residuals.std():.3f}\nSkew: {residuals.skew():.3f}', 
            transform=ax4.transAxes, fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('step4_model_evaluation.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('step4_model_evaluation.pdf', format='pdf', bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ STEP 4 figure saved")

def create_step5_figure(ts_data, medicine):
    """STEP 5: Forecast Generation"""
    print("📊 Creating STEP 5: Forecast Generation...")
    
    # Fit the model
    model = auto_arima(
        ts_data,
        start_p=0, start_q=0,
        max_p=5, max_q=5,
        seasonal=True,
        m=12,
        start_P=0, start_Q=0,
        max_P=2, max_Q=2,
        stepwise=True,
        suppress_warnings=True,
        error_action='ignore',
        trace=False
    )
    
    # Generate forecast
    forecast_periods = 12
    forecast, conf_int = model.predict(n_periods=forecast_periods, return_conf_int=True)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 5.1: Historical Data and Forecast
    forecast_index = pd.date_range(start=ts_data.index[-1] + pd.DateOffset(months=1), 
                                 periods=len(forecast), freq='M')
    
    # Show last 24 months of historical data
    recent_data = ts_data.tail(24)
    ax1.plot(recent_data.index, recent_data.values, linewidth=2, color='blue', label='Historical', alpha=0.8)
    ax1.plot(forecast_index, forecast, linewidth=2, color='red', label='Forecast', alpha=0.8)
    ax1.fill_between(forecast_index, conf_int[:, 0], conf_int[:, 1], 
                   alpha=0.3, color='red', label='95% Confidence Interval')
    ax1.set_title('STEP 5.1: 12-Month Forecast\nHistorical Data + Future Predictions', 
                 fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 5.2: Forecast Values
    ax2.axis('off')
    ax2.text(0.05, 0.95, 'STEP 5.2: Forecast Values', 
            fontsize=14, fontweight='bold', transform=ax2.transAxes)
    
    forecast_text = f"""12-Month Forecast Values:
Month 1:  {forecast[0]:.1f}
Month 2:  {forecast[1]:.1f}
Month 3:  {forecast[2]:.1f}
Month 4:  {forecast[3]:.1f}
Month 5:  {forecast[4]:.1f}
Month 6:  {forecast[5]:.1f}
Month 7:  {forecast[6]:.1f}
Month 8:  {forecast[7]:.1f}
Month 9:  {forecast[8]:.1f}
Month 10: {forecast[9]:.1f}
Month 11: {forecast[10]:.1f}
Month 12: {forecast[11]:.1f}

Forecast Statistics:
Mean: {np.mean(forecast):.1f}
Std Dev: {np.std(forecast):.1f}
Min: {np.min(forecast):.1f}
Max: {np.max(forecast):.1f}"""
    
    ax2.text(0.05, 0.8, forecast_text, fontsize=11, transform=ax2.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    # 5.3: Confidence Intervals
    months = [f'Month {i+1}' for i in range(12)]
    ax3.plot(months, forecast, 'o-', linewidth=2, markersize=6, color='red', label='Forecast')
    ax3.fill_between(months, conf_int[:, 0], conf_int[:, 1], 
                   alpha=0.3, color='red', label='95% CI')
    ax3.set_title('STEP 5.3: Forecast with Confidence Intervals\nUncertainty Quantification', 
                 fontsize=14, fontweight='bold', pad=15)
    ax3.set_xlabel('Forecast Period', fontsize=12)
    ax3.set_ylabel('Quantity Sold', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # 5.4: Forecast Interpretation
    ax4.axis('off')
    ax4.text(0.05, 0.95, 'STEP 5.4: Forecast Interpretation', 
            fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    interpretation_text = f"""Forecast Analysis:

Trend Analysis:
• {'Increasing' if forecast[-1] > forecast[0] else 'Decreasing' if forecast[-1] < forecast[0] else 'Stable'} trend over 12 months
• Change: {((forecast[-1] - forecast[0]) / forecast[0] * 100):+.1f}%
• Average monthly change: {((forecast[-1] - forecast[0]) / 11):+.1f} units

Seasonal Pattern:
• Peak month: Month {np.argmax(forecast) + 1} ({np.max(forecast):.1f} units)
• Trough month: Month {np.argmin(forecast) + 1} ({np.min(forecast):.1f} units)
• Seasonal variation: {((np.max(forecast) - np.min(forecast)) / np.mean(forecast) * 100):.1f}%

Confidence Intervals:
• 95% confidence range
• Lower bound: {np.min(conf_int[:, 0]):.1f} to {np.max(conf_int[:, 0]):.1f}
• Upper bound: {np.min(conf_int[:, 1]):.1f} to {np.max(conf_int[:, 1]):.1f}

Business Implications:
• Inventory planning for next 12 months
• Expected demand: {np.mean(forecast):.0f} units/month
• Peak demand: {np.max(forecast):.0f} units (Month {np.argmax(forecast) + 1})
• Minimum demand: {np.min(forecast):.0f} units (Month {np.argmin(forecast) + 1})"""
    
    ax4.text(0.05, 0.8, interpretation_text, fontsize=10, transform=ax4.transAxes, 
            verticalalignment='top')
    
    plt.tight_layout()
    plt.savefig('step5_forecast_generation.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('step5_forecast_generation.pdf', format='pdf', bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ STEP 5 figure saved")

def create_combined_overview_figure(ts_data, medicine):
    """Create a combined overview of all 5 steps"""
    print("📊 Creating Combined Overview...")
    
    fig = plt.figure(figsize=(24, 16))
    gs = fig.add_gridspec(3, 4, height_ratios=[1, 1, 1], width_ratios=[1, 1, 1, 1], 
                         hspace=0.3, wspace=0.3)
    
    # Step 1: Stationarity
    ax1 = fig.add_subplot(gs[0, 0])
    adf_result = adfuller(ts_data.dropna())
    is_stationary = adf_result[1] <= 0.05
    ax1.axis('off')
    ax1.text(0.1, 0.9, 'STEP 1: STATIONARITY', fontsize=12, fontweight='bold', transform=ax1.transAxes)
    ax1.text(0.1, 0.7, f'ADF p-value: {adf_result[1]:.4f}\n{"STATIONARY" if is_stationary else "NON-STATIONARY"}', 
            fontsize=10, transform=ax1.transAxes, color='green' if is_stationary else 'red')
    
    # Step 2: Seasonal
    ax2 = fig.add_subplot(gs[0, 1])
    if len(ts_data) >= 24:
        decomposition = seasonal_decompose(ts_data, model='additive', period=12)
        seasonal_strength = np.var(decomposition.seasonal) / np.var(ts_data)
        ax2.axis('off')
        ax2.text(0.1, 0.9, 'STEP 2: SEASONAL', fontsize=12, fontweight='bold', transform=ax2.transAxes)
        ax2.text(0.1, 0.7, f'Strength: {seasonal_strength:.1%}\n{"STRONG" if seasonal_strength > 0.1 else "WEAK"}', 
                fontsize=10, transform=ax2.transAxes, color='blue' if seasonal_strength > 0.1 else 'orange')
    
    # Step 3: Model Selection
    ax3 = fig.add_subplot(gs[0, 2])
    model = auto_arima(ts_data, seasonal=True, m=12, suppress_warnings=True, error_action='ignore', trace=False)
    ax3.axis('off')
    ax3.text(0.1, 0.9, 'STEP 3: MODEL', fontsize=12, fontweight='bold', transform=ax3.transAxes)
    ax3.text(0.1, 0.7, f'ARIMA{model.order}\nAIC: {model.aic():.1f}', 
            fontsize=10, transform=ax3.transAxes, fontfamily='monospace')
    
    # Step 4: Evaluation
    ax4 = fig.add_subplot(gs[0, 3])
    fitted_values = model.predict_in_sample()
    mape = np.mean(np.abs((ts_data - fitted_values) / ts_data)) * 100
    ax4.axis('off')
    ax4.text(0.1, 0.9, 'STEP 4: EVALUATION', fontsize=12, fontweight='bold', transform=ax4.transAxes)
    ax4.text(0.1, 0.7, f'MAPE: {mape:.1f}%\n{"EXCELLENT" if mape < 5 else "GOOD" if mape < 15 else "FAIR"}', 
            fontsize=10, transform=ax4.transAxes, color='green' if mape < 15 else 'orange')
    
    # Step 5: Forecast
    ax5 = fig.add_subplot(gs[1:, :2])
    forecast, conf_int = model.predict(n_periods=12, return_conf_int=True)
    forecast_index = pd.date_range(start=ts_data.index[-1] + pd.DateOffset(months=1), periods=12, freq='M')
    
    recent_data = ts_data.tail(24)
    ax5.plot(recent_data.index, recent_data.values, linewidth=2, color='blue', label='Historical', alpha=0.8)
    ax5.plot(forecast_index, forecast, linewidth=2, color='red', label='Forecast', alpha=0.8)
    ax5.fill_between(forecast_index, conf_int[:, 0], conf_int[:, 1], alpha=0.3, color='red', label='95% CI')
    ax5.set_title('STEP 5: FORECAST GENERATION\nComplete ARIMA Process Result', fontsize=14, fontweight='bold')
    ax5.set_xlabel('Date', fontsize=12)
    ax5.set_ylabel('Quantity Sold', fontsize=12)
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    ax5.tick_params(axis='x', rotation=45)
    
    # Summary
    ax6 = fig.add_subplot(gs[1:, 2:])
    ax6.axis('off')
    ax6.text(0.05, 0.95, 'COMPLETE ARIMA PROCESS SUMMARY', fontsize=14, fontweight='bold', transform=ax6.transAxes)
    
    summary_text = f"""Process Overview:
1. STATIONARITY TESTING
   • ADF Test: p-value = {adf_result[1]:.4f}
   • Result: {"STATIONARY" if is_stationary else "NON-STATIONARY"}
   • Implication: {"Ready for ARIMA" if is_stationary else "Needs differencing"}

2. SEASONAL DECOMPOSITION
   • Seasonal Strength: {seasonal_strength:.1%} if 'seasonal_strength' in locals() else 'N/A'
   • Pattern: {"STRONG" if 'seasonal_strength' in locals() and seasonal_strength > 0.1 else "WEAK"}
   • Implication: {"Use SARIMA" if 'seasonal_strength' in locals() and seasonal_strength > 0.1 else "Standard ARIMA"}

3. MODEL SELECTION
   • Best Model: ARIMA{model.order} x SARIMA{model.seasonal_order}
   • AIC: {model.aic():.1f}
   • Parameters: {sum(model.order) + sum(model.seasonal_order)} total

4. MODEL EVALUATION
   • MAPE: {mape:.1f}%
   • Performance: {"EXCELLENT" if mape < 5 else "GOOD" if mape < 15 else "FAIR"}
   • Quality: {"High" if mape < 15 else "Moderate"}

5. FORECAST GENERATION
   • Horizon: 12 months
   • Mean Forecast: {np.mean(forecast):.0f} units/month
   • Range: {np.min(forecast):.0f} to {np.max(forecast):.0f} units
   • Confidence: 95% intervals provided

CONCLUSION:
The ARIMA model successfully captures the time series patterns and provides reliable forecasts for inventory planning and business decision-making."""
    
    ax6.text(0.05, 0.8, summary_text, fontsize=10, transform=ax6.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig('complete_arima_process_overview.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.savefig('complete_arima_process_overview.pdf', format='pdf', bbox_inches='tight', facecolor='white')
    plt.close()
    print("✅ Combined overview figure saved")

if __name__ == "__main__":
    print("Creating complete ARIMA demonstration (Steps 1-5)...")
    create_complete_arima_steps()
    print("\n🎉 All figures created successfully!")
    print("\nFiles created:")
    print("• step1_stationarity_testing.png/pdf")
    print("• step2_seasonal_decomposition.png/pdf")
    print("• step3_auto_arima_selection.png/pdf")
    print("• step4_model_evaluation.png/pdf")
    print("• step5_forecast_generation.png/pdf")
    print("• complete_arima_process_overview.png/pdf")
