#!/usr/bin/env python3
"""
Demonstrate Auto ARIMA Stepwise Search Process for Metformin Data
Shows the AIC minimization process and model selection with detailed output
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
import warnings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from analytics.services import ARIMAForecastingService
from inventory.models import Medicine
from pmdarima import auto_arima
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose

warnings.filterwarnings('ignore')

def demonstrate_auto_arima_process():
    """Demonstrate the complete Auto ARIMA process with detailed output"""
    print("=" * 80)
    print("AUTO ARIMA STEPWISE SEARCH DEMONSTRATION")
    print("Metformin 500mg Sales Data Analysis")
    print("=" * 80)
    
    try:
        # Initialize forecasting service
        service = ARIMAForecastingService()
        
        # Get Metformin data
        metformin = Medicine.objects.get(id=4)
        print(f"✅ Medicine: {metformin.name}")
        
        # Prepare monthly data for analysis
        monthly_data = service.prepare_sales_data(4, 'monthly')
        
        if len(monthly_data) == 0:
            print("❌ No monthly data available for Metformin")
            return
        
        print(f"📊 Data Points: {len(monthly_data)}")
        print(f"📅 Date Range: {monthly_data['date'].min()} to {monthly_data['date'].max()}")
        print()
        
        # Prepare time series data
        ts_data = monthly_data.set_index('date')['quantity']
        ts_data = ts_data.fillna(ts_data.mean())
        
        # Step 1: Stationarity Testing
        print("STEP 1: STATIONARITY TESTING")
        print("-" * 40)
        perform_stationarity_tests(ts_data)
        print()
        
        # Step 2: Seasonal Decomposition
        print("STEP 2: SEASONAL DECOMPOSITION")
        print("-" * 40)
        perform_seasonal_decomposition(ts_data)
        print()
        
        # Step 3: Auto ARIMA Stepwise Search
        print("STEP 3: AUTO ARIMA STEPWISE SEARCH")
        print("-" * 40)
        perform_auto_arima_search(ts_data)
        print()
        
        # Step 4: Model Evaluation
        print("STEP 4: MODEL EVALUATION")
        print("-" * 40)
        evaluate_selected_model(ts_data)
        print()
        
        # Step 5: Forecast Generation
        print("STEP 5: FORECAST GENERATION")
        print("-" * 40)
        generate_forecast(ts_data)
        
    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
        import traceback
        traceback.print_exc()

def perform_stationarity_tests(ts_data):
    """Perform stationarity tests on the time series data"""
    print("Testing stationarity of Metformin sales data...")
    
    # ADF Test
    adf_result = adfuller(ts_data.dropna())
    print(f"Augmented Dickey-Fuller Test:")
    print(f"  ADF Statistic: {adf_result[0]:.6f}")
    print(f"  p-value: {adf_result[1]:.6f}")
    print(f"  Critical Values:")
    for key, value in adf_result[4].items():
        print(f"    {key}: {value:.6f}")
    
    if adf_result[1] <= 0.05:
        print("  ✅ Data is STATIONARY (p-value ≤ 0.05)")
    else:
        print("  ❌ Data is NON-STATIONARY (p-value > 0.05)")
        print("  🔄 Differencing will be required")
    
    # Data statistics
    print(f"\nData Statistics:")
    print(f"  Mean: {ts_data.mean():.2f}")
    print(f"  Std Dev: {ts_data.std():.2f}")
    print(f"  Min: {ts_data.min():.2f}")
    print(f"  Max: {ts_data.max():.2f}")

def perform_seasonal_decomposition(ts_data):
    """Perform seasonal decomposition analysis"""
    print("Analyzing seasonal patterns...")
    
    if len(ts_data) >= 24:  # At least 2 years of data
        try:
            decomposition = seasonal_decompose(ts_data, model='additive', period=12)
            
            print("Seasonal Decomposition Results:")
            print(f"  Trend Component: {'Present' if decomposition.trend.notna().any() else 'Not detected'}")
            print(f"  Seasonal Component: {'Present' if decomposition.seasonal.notna().any() else 'Not detected'}")
            print(f"  Residual Component: {'Present' if decomposition.resid.notna().any() else 'Not detected'}")
            
            # Calculate seasonal strength
            seasonal_strength = np.var(decomposition.seasonal) / np.var(ts_data)
            print(f"  Seasonal Strength: {seasonal_strength:.4f}")
            
            if seasonal_strength > 0.1:
                print("  ✅ Strong seasonal pattern detected")
            else:
                print("  ⚠️  Weak seasonal pattern")
                
        except Exception as e:
            print(f"  ❌ Error in seasonal decomposition: {e}")
    else:
        print("  ⚠️  Insufficient data for seasonal decomposition (need ≥24 months)")

def perform_auto_arima_search(ts_data):
    """Perform Auto ARIMA stepwise search with detailed output"""
    print("Performing stepwise search to minimize AIC...")
    print()
    
    # Configure Auto ARIMA with detailed output
    model = auto_arima(
        ts_data,
        start_p=0, start_q=0,
        max_p=5, max_q=5,
        seasonal=True,  # Enable seasonal analysis
        m=12,  # Monthly seasonality
        start_P=0, start_Q=0,
        max_P=2, max_Q=2,
        stepwise=True,
        suppress_warnings=False,  # Show warnings for demonstration
        error_action='ignore',
        trace=True,  # Show detailed search process
        random_state=42
    )
    
    print(f"\n✅ Auto ARIMA Search Completed!")
    print(f"Best Model: {model.order} x {model.seasonal_order}")
    print(f"Final AIC: {model.aic():.3f}")
    print(f"Final BIC: {model.bic():.3f}")
    
    # Extract parameters
    p, d, q = model.order
    P, D, Q, m = model.seasonal_order
    
    print(f"\nModel Parameters:")
    print(f"  Non-seasonal: ARIMA({p},{d},{q})")
    print(f"  Seasonal: SARIMA({P},{D},{Q})[{m}]")
    print(f"  Total Parameters: {p + d + q + P + D + Q}")
    
    return model

def evaluate_selected_model(ts_data):
    """Evaluate the selected model with comprehensive metrics"""
    print("Evaluating selected model...")
    
    # Fit the best model
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
    
    # Get model summary
    print(f"Model Summary:")
    print(f"  AIC: {model.aic():.3f}")
    print(f"  BIC: {model.bic():.3f}")
    print(f"  Model Order: {model.order}")
    print(f"  Seasonal Order: {model.seasonal_order}")
    
    # Calculate additional metrics
    fitted_values = model.predict_in_sample()
    residuals = ts_data - fitted_values
    
    # RMSE
    rmse = np.sqrt(np.mean(residuals**2))
    print(f"  RMSE: {rmse:.3f}")
    
    # MAE
    mae = np.mean(np.abs(residuals))
    print(f"  MAE: {mae:.3f}")
    
    # MAPE
    mape = np.mean(np.abs(residuals / ts_data)) * 100
    print(f"  MAPE: {mape:.2f}%")
    
    # Model quality assessment
    if mape < 5:
        quality = "Excellent"
    elif mape < 15:
        quality = "Good"
    elif mape < 25:
        quality = "Fair"
    else:
        quality = "Poor"
    
    print(f"  Model Quality: {quality}")
    
    return model

def generate_forecast(ts_data):
    """Generate forecast using the selected model"""
    print("Generating forecast...")
    
    # Fit model
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
    forecast_periods = 12  # 12 months ahead
    forecast, conf_int = model.predict(n_periods=forecast_periods, return_conf_int=True)
    
    print(f"Forecast for next {forecast_periods} months:")
    print(f"  Forecast Values: {[round(x, 2) for x in forecast]}")
    print(f"  Confidence Intervals: {[round(x, 2) for x in conf_int[0]]} to {[round(x, 2) for x in conf_int[1]]}")
    
    # Calculate forecast statistics
    forecast_mean = np.mean(forecast)
    forecast_std = np.std(forecast)
    
    print(f"\nForecast Statistics:")
    print(f"  Mean Forecast: {forecast_mean:.2f}")
    print(f"  Std Deviation: {forecast_std:.2f}")
    print(f"  Min Forecast: {np.min(forecast):.2f}")
    print(f"  Max Forecast: {np.max(forecast):.2f}")
    
    return model, forecast, conf_int

def create_visualization(ts_data, model, forecast, conf_int):
    """Create visualization of the analysis"""
    print("\nCreating visualization...")
    
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Plot 1: Original Time Series
        ax1.plot(ts_data.index, ts_data.values, label='Actual Sales', linewidth=2, color='blue')
        ax1.set_title('Metformin 500mg - Monthly Sales Data', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Quantity Sold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Seasonal Decomposition
        if len(ts_data) >= 24:
            decomposition = seasonal_decompose(ts_data, model='additive', period=12)
            ax2.plot(ts_data.index, decomposition.trend, label='Trend', linewidth=2)
            ax2.plot(ts_data.index, decomposition.seasonal, label='Seasonal', linewidth=2)
            ax2.set_title('Seasonal Decomposition', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Plot 3: Model Fit
        fitted_values = model.predict_in_sample()
        ax3.plot(ts_data.index, ts_data.values, label='Actual', linewidth=2, color='blue')
        ax3.plot(ts_data.index, fitted_values, label='Fitted', linewidth=2, color='red')
        ax3.set_title('Model Fit Comparison', fontsize=14, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Forecast
        forecast_index = pd.date_range(start=ts_data.index[-1] + pd.DateOffset(months=1), 
                                     periods=len(forecast), freq='M')
        ax4.plot(ts_data.index[-24:], ts_data.values[-24:], label='Historical', linewidth=2, color='blue')
        ax4.plot(forecast_index, forecast, label='Forecast', linewidth=2, color='red')
        ax4.fill_between(forecast_index, conf_int[:, 0], conf_int[:, 1], 
                        alpha=0.3, color='red', label='Confidence Interval')
        ax4.set_title('12-Month Forecast', fontsize=14, fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the plot
        output_path = 'metformin_auto_arima_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✅ Visualization saved as: {output_path}")
        
        plt.show()
        
    except Exception as e:
        print(f"❌ Error creating visualization: {e}")

if __name__ == "__main__":
    print("Starting Auto ARIMA demonstration for Metformin data...")
    demonstrate_auto_arima_process()
    print("\n🎉 Demonstration completed successfully!")
