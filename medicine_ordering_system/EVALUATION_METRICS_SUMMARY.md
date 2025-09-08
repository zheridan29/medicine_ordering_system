# Evaluation Metrics Summary - Medicine Ordering System

## Overview
This document provides a comprehensive overview of all evaluation metrics implemented and used in the medicine ordering system's forecasting analytics.

## ✅ Complete Evaluation Metrics Implementation

### 1. AIC (Akaike Information Criterion)
- **📍 Database Field**: `DemandForecast.aic` (FloatField)
- **📍 Implementation**: `analytics/services.py` (line 341)
- **🎯 Purpose**: Model selection - lower values indicate better model performance
- **🔧 Usage**: Selecting best-performing forecasts per medicine
- **📊 Source**: `fitted_model.aic` from ARIMA model
- **💾 Storage**: Permanently stored in database

### 2. BIC (Bayesian Information Criterion)
- **📍 Database Field**: `DemandForecast.bic` (FloatField)
- **📍 Implementation**: `analytics/services.py` (line 342)
- **🎯 Purpose**: Model selection - lower values indicate better model performance
- **🔧 Usage**: Model comparison and selection
- **📊 Source**: `fitted_model.bic` from ARIMA model
- **💾 Storage**: Permanently stored in database

### 3. RMSE (Root Mean Square Error)
- **📍 Database Field**: `DemandForecast.rmse` (FloatField)
- **📍 Implementation**: `analytics/services.py` (line 229)
- **🎯 Purpose**: Forecast accuracy measurement - lower values indicate better accuracy
- **🔧 Usage**: Measuring forecast accuracy
- **📊 Source**: `sqrt(mean_squared_error(actual, predicted))`
- **💾 Storage**: Permanently stored in database

### 4. MAE (Mean Absolute Error)
- **📍 Database Field**: `DemandForecast.mae` (FloatField)
- **📍 Implementation**: `analytics/services.py` (line 230)
- **🎯 Purpose**: Forecast accuracy measurement - lower values indicate better accuracy
- **🔧 Usage**: Measuring average forecast error
- **📊 Source**: `mean_absolute_error(actual, predicted)`
- **💾 Storage**: Permanently stored in database

### 5. MAPE (Mean Absolute Percentage Error)
- **📍 Database Field**: `DemandForecast.mape` (FloatField)
- **📍 Implementation**: `analytics/services.py` (line 233)
- **🎯 Purpose**: Forecast accuracy percentage - lower values indicate better accuracy
- **🔧 Usage**: Measuring relative forecast error as percentage
- **📊 Source**: `mean(|actual - predicted| / actual) * 100`
- **💾 Storage**: Permanently stored in database

### 6. ACF (Autocorrelation Function)
- **📍 Implementation**: `analytics/services.py` (line 246)
- **🎯 Purpose**: Time series analysis and pattern identification
- **🔧 Usage**: Model diagnostics and validation
- **📊 Source**: `statsmodels.tsa.stattools.acf()`
- **💾 Storage**: Calculated on-demand (not stored)

### 7. PACF (Partial Autocorrelation Function)
- **📍 Implementation**: `analytics/services.py` (line 247)
- **🎯 Purpose**: Time series analysis and AR order identification
- **🔧 Usage**: Model diagnostics and validation
- **📊 Source**: `statsmodels.tsa.stattools.pacf()`
- **💾 Storage**: Calculated on-demand (not stored)

## 🎯 How Metrics Are Used

### Model Selection
- **AIC/BIC**: Used to select the best-performing forecast per medicine
- **Selection Logic**: Lower values indicate better model performance
- **Implementation**: `_get_best_forecasts_per_medicine()` method in `analytics/views.py`

### Forecast Accuracy Measurement
- **RMSE/MAE/MAPE**: Measure how accurate the forecasts are
- **RMSE**: Penalizes larger errors more heavily
- **MAE**: Provides average error magnitude
- **MAPE**: Shows relative error as percentage

### Model Diagnostics
- **ACF/PACF**: Help validate ARIMA model assumptions
- **ACF**: Identifies autocorrelation patterns in time series
- **PACF**: Helps determine optimal AR order for ARIMA model

## 📊 Where Metrics Are Displayed

### Full Analytics Dashboard
- **Location**: `/analytics/dashboard/`
- **Display**: All metrics shown in forecast management section
- **Features**: Model evaluation tables, performance comparisons
- **Access**: Admin role only

### Model Evaluation Page
- **Location**: `/analytics/model-evaluation/`
- **Display**: Detailed metrics table with all values
- **Features**: Performance over time charts, model quality assessments
- **Access**: Admin role only

### Forecast-Only View
- **Location**: `/analytics/forecast-only/`
- **Display**: AIC and MAPE shown in model info cards
- **Features**: Focus on key performance indicators
- **Access**: Admin and Pharmacist roles

### API Responses
- **Endpoints**: `/analytics/api/forecast/`
- **Display**: All metrics included in forecast data
- **Features**: Available for external integrations
- **Access**: Authenticated users

## 🔧 Technical Implementation Details

### Database Schema
```python
class DemandForecast(models.Model):
    # Model evaluation metrics
    aic = models.FloatField()  # Akaike Information Criterion
    bic = models.FloatField()  # Bayesian Information Criterion
    rmse = models.FloatField()  # Root Mean Square Error
    mae = models.FloatField()   # Mean Absolute Error
    mape = models.FloatField()  # Mean Absolute Percentage Error
```

### Calculation Methods
```python
def calculate_model_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """Calculate RMSE, MAE, and MAPE"""
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    mae = mean_absolute_error(actual, predicted)
    mape = np.mean(np.abs((actual - predicted) / np.where(actual != 0, actual, 1))) * 100
    
def calculate_acf_pacf(self, data: pd.Series, nlags: int = 20) -> Dict[str, List[float]]:
    """Calculate ACF and PACF values"""
    acf_values = acf(data.dropna(), nlags=nlags, fft=False)
    pacf_values = pacf(data.dropna(), nlags=nlags)
```

## 📈 Performance Thresholds

### Data Quality Requirements
- **Minimum Data Points**: 30 for daily, 12 for weekly, 6 for monthly
- **Data Consistency**: No major gaps in time series
- **Seasonality**: Full seasonal cycles for better accuracy

### Model Selection Criteria
- **Primary**: AIC (Akaike Information Criterion)
- **Secondary**: BIC (Bayesian Information Criterion)
- **Fallback**: RMSE if AIC/BIC are unavailable

### Accuracy Benchmarks
- **Excellent MAPE**: < 10%
- **Good MAPE**: 10-20%
- **Acceptable MAPE**: 20-30%
- **Poor MAPE**: > 30%

## 🚀 Future Enhancements

### Potential Additions
- **MASE**: Mean Absolute Scaled Error
- **SMAPE**: Symmetric Mean Absolute Percentage Error
- **Theil's U**: Theil's Inequality Coefficient
- **Diebold-Mariano Test**: Statistical significance testing

### Monitoring Capabilities
- **Real-time Metrics**: Live performance monitoring
- **Alert System**: Threshold-based notifications
- **Trend Analysis**: Historical performance tracking

## ✅ Conclusion

**All 6 evaluation metrics (AIC, BIC, RMSE, MAE, MAPE, ACF, PACF) are fully implemented and actively used in the medicine ordering system.** They serve complementary purposes in model selection, accuracy measurement, and diagnostic validation, providing a comprehensive framework for evaluating forecasting performance.

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**System Version**: Medicine Ordering System v2.0
