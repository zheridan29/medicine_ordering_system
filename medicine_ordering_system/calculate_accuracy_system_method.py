#!/usr/bin/env python3
"""
Script to calculate MAE, MAPE, MSE, RMSE using the EXACT same method as the system
"""

import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.metrics import mean_squared_error, mean_absolute_error

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medicine_ordering_system.settings')
django.setup()

from pmdarima import auto_arima
from analytics.services import ARIMAForecastingService
from inventory.models import Medicine

def calculate_accuracy_metrics_system_method():
    """Calculate MAE, MAPE, MSE, RMSE using the EXACT same method as the system"""
    
    print("📊 Calculating ARIMA Model Accuracy Metrics (System Method)")
    print("=" * 70)
    
    # Get Metformin data
    service = ARIMAForecastingService()
    medicine = Medicine.objects.get(name__icontains='Metformin')
    
    # Prepare data using the system's method
    df = service.prepare_sales_data(medicine.id, 'monthly')
    ts_data = df.set_index('date')['quantity']
    
    print(f"Data shape: {ts_data.shape}")
    print(f"Date range: {ts_data.index.min()} to {ts_data.index.max()}")
    print()
    
    # Split data into training and testing sets
    split_point = int(len(ts_data) * 0.8)  # 80% for training, 20% for testing
    train_data = ts_data[:split_point]
    test_data = ts_data[split_point:]
    
    print(f"Training data: {len(train_data)} months ({train_data.index[0]} to {train_data.index[-1]})")
    print(f"Testing data: {len(test_data)} months ({test_data.index[0]} to {test_data.index[-1]})")
    print()
    
    # Use the SAME model that was already identified: ARIMA(0,1,2)(1,0,0)[12]
    print("Using the identified optimal model: ARIMA(0,1,2)(1,0,0)[12]")
    print("Fitting the model on training data...")
    
    # Import the specific ARIMA model
    from statsmodels.tsa.arima.model import ARIMA
    
    # Fit the SAME model that was identified earlier
    model = ARIMA(train_data, order=(0,1,2), seasonal_order=(1,0,0,12))
    fitted_model = model.fit()
    
    print(f"Model: ARIMA(0,1,2)(1,0,0)[12]")
    print(f"Model AIC: {fitted_model.aic:.2f}")
    print()
    
    # Generate predictions for test period
    print("Generating predictions for test period...")
    predictions = fitted_model.forecast(steps=len(test_data))
    
    # Align predictions with test data
    pred_series = pd.Series(predictions, index=test_data.index)
    
    print(f"Predictions generated: {len(predictions)} periods")
    print()
    
    # Use the EXACT same method as the system
    print("CALCULATING ACCURACY METRICS (System Method):")
    print("-" * 50)
    
    # Convert to numpy arrays as the system does
    actual = test_data.values
    predicted = pred_series.values
    
    print("Using system's calculate_model_metrics method...")
    
    # Use the system's exact method
    metrics = service.calculate_model_metrics(actual, predicted)
    
    print(f"RMSE (Root Mean Square Error): {metrics['rmse']:.2f}")
    print("  → Square root of MSE (same units as original data)")
    print("  → Lower is better (same units as original data)")
    print("  → More sensitive to large errors than MAE")
    print()
    
    print(f"MAE (Mean Absolute Error): {metrics['mae']:.2f}")
    print("  → Average absolute difference between predicted and actual values")
    print("  → Lower is better (same units as original data)")
    print("  → Less sensitive to outliers than RMSE")
    print()
    
    print(f"MAPE (Mean Absolute Percentage Error): {metrics['mape']:.2f}%")
    print("  → Average percentage error between predicted and actual values")
    print("  → Lower is better (percentage scale)")
    print("  → MAPE < 10% is considered excellent")
    print()
    
    # Calculate MSE (not in system but useful)
    mse = mean_squared_error(actual, predicted)
    print(f"MSE (Mean Squared Error): {mse:.2f}")
    print("  → Average squared difference between predicted and actual values")
    print("  → Lower is better (squared units)")
    print("  → More sensitive to large errors than MAE")
    print()
    
    # Additional metrics using system's approach
    print("ADDITIONAL EVALUATION METRICS:")
    print("-" * 50)
    
    # R-squared
    ss_res = np.sum((actual - predicted) ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    print(f"R-squared: {r_squared:.4f}")
    print("  → Proportion of variance explained by the model")
    print("  → Higher is better (0-1 scale, 1 = perfect fit)")
    print()
    
    # Mean Error (Bias)
    mean_error = np.mean(actual - predicted)
    print(f"Mean Error (Bias): {mean_error:.2f}")
    print("  → Average difference between predicted and actual values")
    print("  → Close to 0 indicates unbiased predictions")
    print()
    
    # Directional Accuracy
    actual_direction = np.diff(actual) > 0
    pred_direction = np.diff(predicted) > 0
    directional_accuracy = np.mean(actual_direction == pred_direction) * 100
    print(f"Directional Accuracy: {directional_accuracy:.1f}%")
    print("  → Percentage of correct trend direction predictions")
    print("  → Higher is better (0-100% scale)")
    print()
    
    # Performance Summary
    print("PERFORMANCE SUMMARY:")
    print("-" * 50)
    print(f"Model: ARIMA(0,1,2)(1,0,0)[12]")
    print(f"Training Period: {train_data.index[0].strftime('%Y-%m')} to {train_data.index[-1].strftime('%Y-%m')}")
    print(f"Testing Period: {test_data.index[0].strftime('%Y-%m')} to {test_data.index[-1].strftime('%Y-%m')}")
    print(f"Test Data Points: {len(test_data)}")
    print()
    print("Accuracy Metrics (System Method):")
    print(f"  RMSE: {metrics['rmse']:.2f} units")
    print(f"  MAE: {metrics['mae']:.2f} units")
    print(f"  MAPE: {metrics['mape']:.2f}%")
    print(f"  MSE: {mse:.2f}")
    print(f"  R²: {r_squared:.4f}")
    print(f"  Directional Accuracy: {directional_accuracy:.1f}%")
    print()
    
    # Performance Interpretation
    print("PERFORMANCE INTERPRETATION:")
    print("-" * 50)
    
    if metrics['mape'] < 5:
        mape_rating = "Excellent"
    elif metrics['mape'] < 10:
        mape_rating = "Very Good"
    elif metrics['mape'] < 20:
        mape_rating = "Good"
    elif metrics['mape'] < 50:
        mape_rating = "Fair"
    else:
        mape_rating = "Poor"
    
    print(f"MAPE Rating: {mape_rating} ({metrics['mape']:.2f}%)")
    
    if r_squared > 0.9:
        r2_rating = "Excellent"
    elif r_squared > 0.8:
        r2_rating = "Very Good"
    elif r_squared > 0.7:
        r2_rating = "Good"
    elif r_squared > 0.5:
        r2_rating = "Fair"
    else:
        r2_rating = "Poor"
    
    print(f"R² Rating: {r2_rating} ({r_squared:.4f})")
    
    if directional_accuracy > 80:
        dir_rating = "Excellent"
    elif directional_accuracy > 70:
        dir_rating = "Good"
    elif directional_accuracy > 60:
        dir_rating = "Fair"
    else:
        dir_rating = "Poor"
    
    print(f"Directional Accuracy Rating: {dir_rating} ({directional_accuracy:.1f}%)")
    
    print()
    print("=" * 70)
    print("✅ Accuracy metrics calculation completed using system method!")

if __name__ == "__main__":
    calculate_accuracy_metrics_system_method()
