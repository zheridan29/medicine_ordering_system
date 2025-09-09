"""
ARIMA Step-by-Step Analysis Functions
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import base64
import io
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
from pmdarima import auto_arima


def generate_step_analysis(ts_data, step, service):
    """
    Generate analysis and visualization for a specific ARIMA step
    """
    step_data = {'step': step}
    
    try:
        if step == '1':
            # STEP 1: Stationarity Testing
            adf_result = adfuller(ts_data.dropna())
            step_data.update({
                'title': 'STEP 1: Stationarity Testing',
                'description': 'Testing if the time series data is stationary using Augmented Dickey-Fuller test',
                'adf_statistic': adf_result[0],
                'p_value': adf_result[1],
                'critical_values': adf_result[4],
                'is_stationary': adf_result[1] <= 0.05,
                'conclusion': 'STATIONARY' if adf_result[1] <= 0.05 else 'NON-STATIONARY',
                'chart': create_step1_chart(ts_data, adf_result)
            })
            
        elif step == '2':
            # STEP 2: Seasonal Decomposition
            if len(ts_data) >= 24:
                decomposition = seasonal_decompose(ts_data, model='additive', period=12)
                seasonal_strength = np.var(decomposition.seasonal) / np.var(ts_data)
                step_data.update({
                    'title': 'STEP 2: Seasonal Decomposition',
                    'description': 'Decomposing the time series into trend, seasonal, and residual components',
                    'trend_present': not decomposition.trend.isna().all(),
                    'seasonal_present': not decomposition.seasonal.isna().all(),
                    'residual_present': not decomposition.resid.isna().all(),
                    'seasonal_strength': seasonal_strength,
                    'strong_seasonal': seasonal_strength > 0.1,
                    'chart': create_step2_chart(ts_data, decomposition)
                })
            else:
                step_data.update({
                    'title': 'STEP 2: Seasonal Decomposition',
                    'description': 'Insufficient data for seasonal decomposition (need at least 24 data points)',
                    'error': 'Insufficient data for seasonal decomposition'
                })
                
        elif step == '3':
            # STEP 3: Auto ARIMA Model Selection
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
            step_data.update({
                'title': 'STEP 3: Auto ARIMA Model Selection',
                'description': 'Automatically selecting the best ARIMA model parameters using information criteria',
                'order': model.order,
                'seasonal_order': model.seasonal_order,
                'aic': model.aic(),
                'bic': model.bic(),
                'total_params': sum(model.order) + sum(model.seasonal_order),
                'chart': create_step3_chart(ts_data, model)
            })
            
        elif step == '4':
            # STEP 4: Model Evaluation
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
            fitted_values = model.predict_in_sample()
            metrics = service.calculate_model_metrics(ts_data.values, fitted_values)
            residuals = ts_data - fitted_values
            
            step_data.update({
                'title': 'STEP 4: Model Evaluation',
                'description': 'Evaluating the ARIMA model performance using various metrics',
                'rmse': metrics['rmse'],
                'mae': metrics['mae'],
                'mape': metrics['mape'],
                'aic': model.aic(),
                'bic': model.bic(),
                'performance': 'Excellent' if metrics['mape'] < 5 else 'Good' if metrics['mape'] < 15 else 'Fair' if metrics['mape'] < 25 else 'Poor',
                'chart': create_step4_chart(ts_data, fitted_values, residuals)
            })
            
        elif step == '5':
            # STEP 5: Forecast Generation
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
            forecast, conf_int = model.predict(n_periods=12, return_conf_int=True)
            
            step_data.update({
                'title': 'STEP 5: Forecast Generation',
                'description': 'Generating 12-month forecasts with confidence intervals',
                'forecast_values': forecast.tolist(),
                'confidence_intervals': conf_int.tolist(),
                'forecast_mean': float(np.mean(forecast)),
                'forecast_std': float(np.std(forecast)),
                'forecast_min': float(np.min(forecast)),
                'forecast_max': float(np.max(forecast)),
                'chart': create_step5_chart(ts_data, forecast, conf_int)
            })
            
    except Exception as e:
        step_data['error'] = f'Step {step} analysis failed: {str(e)}'
    
    return step_data


def create_step1_chart(ts_data, adf_result):
    """Create chart for Step 1: Stationarity Testing"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Original time series
    ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='#2E86AB', marker='o', markersize=3)
    ax1.set_title('Original Time Series', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Add trend line
    z = np.polyfit(range(len(ts_data)), ts_data.values, 1)
    p = np.poly1d(z)
    ax1.plot(ts_data.index, p(range(len(ts_data))), "r--", alpha=0.8, linewidth=2, label='Trend Line')
    ax1.legend()
    
    # ADF Test Results
    ax2.axis('off')
    ax2.text(0.05, 0.95, 'Augmented Dickey-Fuller Test Results', 
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
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"


def create_step2_chart(ts_data, decomposition):
    """Create chart for Step 2: Seasonal Decomposition"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
    
    # Original Data
    ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='blue', label='Original')
    ax1.set_title('Original Time Series', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Trend Component
    ax2.plot(ts_data.index, decomposition.trend, linewidth=2, color='red', label='Trend')
    ax2.set_title('Trend Component', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Trend Value', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Seasonal Component
    ax3.plot(ts_data.index, decomposition.seasonal, linewidth=2, color='green', label='Seasonal')
    ax3.set_title('Seasonal Component', fontsize=14, fontweight='bold', pad=15)
    ax3.set_xlabel('Date', fontsize=12)
    ax3.set_ylabel('Seasonal Value', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # Residual Component
    ax4.plot(ts_data.index, decomposition.resid, linewidth=2, color='orange', label='Residual')
    ax4.set_title('Residual Component', fontsize=14, fontweight='bold', pad=15)
    ax4.set_xlabel('Date', fontsize=12)
    ax4.set_ylabel('Residual Value', fontsize=12)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"


def create_step3_chart(ts_data, model):
    """Create chart for Step 3: Auto ARIMA Model Selection"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Model Selection Process
    ax1.axis('off')
    ax1.text(0.05, 0.95, 'Auto ARIMA Model Selection Process', 
            fontsize=14, fontweight='bold', transform=ax1.transAxes)
    
    process_text = f"""Search Strategy:
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
    
    ax1.text(0.05, 0.8, process_text, fontsize=11, transform=ax1.transAxes, 
            verticalalignment='top')
    
    # Selected Model
    ax2.axis('off')
    ax2.text(0.05, 0.95, 'Selected ARIMA Model', 
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
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"


def create_step4_chart(ts_data, fitted_values, residuals):
    """Create chart for Step 4: Model Evaluation"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
    
    # Model Fit Comparison
    ax1.plot(ts_data.index, ts_data.values, linewidth=2, color='blue', label='Actual', alpha=0.8)
    ax1.plot(ts_data.index, fitted_values, linewidth=2, color='red', label='Fitted', alpha=0.8)
    ax1.set_title('Model Fit Comparison', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Residuals Analysis
    ax2.plot(ts_data.index, residuals, linewidth=1, color='green', alpha=0.7)
    ax2.axhline(y=0, color='red', linestyle='--', alpha=0.8)
    ax2.set_title('Residuals Analysis', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Residuals', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Residuals Distribution
    ax3.hist(residuals, bins=20, alpha=0.7, color='skyblue', edgecolor='navy')
    ax3.axvline(x=0, color='red', linestyle='--', linewidth=2)
    ax3.set_title('Residuals Distribution', fontsize=14, fontweight='bold', pad=15)
    ax3.set_xlabel('Residual Value', fontsize=12)
    ax3.set_ylabel('Frequency', fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # Evaluation Metrics
    rmse = np.sqrt(np.mean(residuals**2))
    mae = np.mean(np.abs(residuals))
    mape = np.mean(np.abs(residuals / ts_data)) * 100
    
    ax4.axis('off')
    ax4.text(0.05, 0.95, 'Model Evaluation Metrics', 
            fontsize=14, fontweight='bold', transform=ax4.transAxes)
    
    metrics_text = f"""Performance Metrics:

RMSE: {rmse:.3f}
• Measures average prediction error
• Penalizes larger errors more
• Same units as original data

MAE: {mae:.3f}
• Measures average absolute error
• Less sensitive to outliers
• Easy to interpret

MAPE: {mape:.2f}%
• Measures relative error as percentage
• Allows comparison across scales
• Lower is better

Performance Rating:
{'Excellent' if mape < 5 else 'Good' if mape < 15 else 'Fair' if mape < 25 else 'Poor'} (MAPE: {mape:.1f}%)"""
    
    ax4.text(0.05, 0.8, metrics_text, fontsize=11, transform=ax4.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"


def create_step5_chart(ts_data, forecast, conf_int):
    """Create chart for Step 5: Forecast Generation"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Historical Data and Forecast
    forecast_index = pd.date_range(start=ts_data.index[-1] + pd.DateOffset(months=1), 
                                 periods=len(forecast), freq='M')
    
    # Show last 24 months of historical data
    recent_data = ts_data.tail(24)
    ax1.plot(recent_data.index, recent_data.values, linewidth=2, color='blue', label='Historical', alpha=0.8)
    ax1.plot(forecast_index, forecast, linewidth=2, color='red', label='Forecast', alpha=0.8)
    ax1.fill_between(forecast_index, conf_int[:, 0], conf_int[:, 1], 
                   alpha=0.3, color='red', label='95% Confidence Interval')
    ax1.set_title('12-Month Forecast with Confidence Intervals', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Quantity Sold', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Forecast Values and Statistics
    ax2.axis('off')
    ax2.text(0.05, 0.95, 'Forecast Analysis', 
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
Max: {np.max(forecast):.1f}

Trend Analysis:
{'Increasing' if forecast[-1] > forecast[0] else 'Decreasing' if forecast[-1] < forecast[0] else 'Stable'} trend
Change: {((forecast[-1] - forecast[0]) / forecast[0] * 100):+.1f}%"""
    
    ax2.text(0.05, 0.8, forecast_text, fontsize=10, transform=ax2.transAxes, 
            verticalalignment='top', fontfamily='monospace')
    
    plt.tight_layout()
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return f"data:image/png;base64,{image_base64}"
