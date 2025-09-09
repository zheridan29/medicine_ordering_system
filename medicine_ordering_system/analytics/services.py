"""
ARIMA forecasting service for demand prediction and supply chain optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from decimal import Decimal
import time
import sqlite3

from pmdarima import auto_arima
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings

from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from django.db import transaction, connection

from .models import DemandForecast, InventoryOptimization, SalesTrend
from inventory.models import Medicine
from orders.models import OrderItem
from transactions.models import Transaction

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


def retry_database_operation(max_retries=3, delay=1):
    """
    Decorator to retry database operations on lock errors
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
                    if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                        logger.warning(f"Database locked on attempt {attempt + 1}, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        raise e
                except Exception as e:
                    raise e
            return None
        return wrapper
    return decorator


class ARIMAForecastingService:
    """
    Service class for ARIMA-based demand forecasting
    """
    
    def __init__(self):
        self.min_data_points = {
            'daily': 30,
            'weekly': 12,
            'monthly': 6
        }
        
    def prepare_sales_data(self, medicine_id: int, period_type: str = 'daily', 
                          start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Prepare sales data for ARIMA forecasting
        """
        if not start_date or not end_date:
            # If no date range specified, find the actual range of available data
            order_items = OrderItem.objects.filter(
                medicine_id=medicine_id,
                order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
            ).order_by('order__created_at')
            
            if not order_items.exists():
                raise ValueError(f"No sales data found for medicine {medicine_id}")
            
            if not start_date:
                start_date = order_items.first().order.created_at
            if not end_date:
                end_date = order_items.last().order.created_at
            
        # Get sales data from OrderItems
        order_items = OrderItem.objects.filter(
            medicine_id=medicine_id,
            order__created_at__range=[start_date, end_date],
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).values('order__created_at', 'quantity').order_by('order__created_at')
        
        if not order_items.exists():
            # Debug: Try without date range filter
            debug_items = OrderItem.objects.filter(
                medicine_id=medicine_id,
                order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
            ).values('order__created_at', 'quantity').order_by('order__created_at')
            
            if not debug_items.exists():
                # Try with any status
                any_status_items = OrderItem.objects.filter(
                    medicine_id=medicine_id
                ).values('order__created_at', 'quantity').order_by('order__created_at')
                
                if not any_status_items.exists():
                    raise ValueError(f"No sales data found for medicine {medicine_id}")
                else:
                    # Use items with any status
                    order_items = any_status_items
                    logger.warning(f"Using order items with any status for medicine {medicine_id}")
            else:
                # Use items without date range
                order_items = debug_items
                logger.warning(f"Using order items without date range for medicine {medicine_id}")
        
        # Convert to DataFrame
        df = pd.DataFrame(list(order_items))
        df['order__created_at'] = pd.to_datetime(df['order__created_at'])
        
        # Debug logging
        logger.info(f"Prepared {len(df)} records for {period_type} forecasting")
        logger.info(f"Date range: {df['order__created_at'].min()} to {df['order__created_at'].max()}")
        
        # Group by period and aggregate quantities
        if period_type == 'daily':
            grouped = df.groupby(df['order__created_at'].dt.to_period('D'))['quantity'].sum()
        elif period_type == 'weekly':
            grouped = df.groupby(df['order__created_at'].dt.to_period('W'))['quantity'].sum()
        elif period_type == 'monthly':
            grouped = df.groupby(df['order__created_at'].dt.to_period('M'))['quantity'].sum()
        else:
            raise ValueError("period_type must be 'daily', 'weekly', or 'monthly'")

        # Debug logging
        logger.info(f"Grouped data for {period_type}: {len(grouped)} periods")
        logger.info(f"Non-zero periods: {(grouped > 0).sum()}")
        logger.info(f"Sample values: {grouped.head()}")

        # Convert period index to datetime and create DataFrame
        df_result = pd.DataFrame({
            'date': grouped.index.to_timestamp(),
            'quantity': grouped.values
        })
        
        # Debug logging
        logger.info(f"DataFrame result shape: {df_result.shape}")
        logger.info(f"DataFrame non-zero: {(df_result['quantity'] > 0).sum()}")
        
        # For now, just return the grouped data without reindexing
        # This will preserve the actual aggregated values
        try:
            # Ensure quantity is numeric and non-negative
            df_result['quantity'] = pd.to_numeric(df_result['quantity'], errors='coerce').fillna(0)
            df_result['quantity'] = df_result['quantity'].clip(lower=0)
            
            # Final debug logging
            logger.info(f"Final DataFrame - Non-zero periods: {(df_result['quantity'] > 0).sum()}")
            logger.info(f"Final DataFrame - Sample values: {df_result['quantity'].head()}")
            
        except Exception as e:
            logger.error(f"Error processing data for {period_type}: {e}")
            logger.error(f"DataFrame columns: {df_result.columns.tolist()}")
            logger.error(f"DataFrame dtypes: {df_result.dtypes}")
            raise ValueError(f"Error processing {period_type} data: {e}")
        
        # Use the result DataFrame
        df = df_result
        
        return df
    
    def find_optimal_arima_params(self, data: pd.Series) -> Tuple[int, int, int]:
        """
        Find optimal ARIMA parameters using auto_arima
        """
        try:
            # Clean data - remove NaN and infinite values
            clean_data = data.dropna()
            if len(clean_data) == 0:
                logger.warning("No valid data points after cleaning, using fallback parameters")
                return 1, 1, 1
            
            # Use auto_arima to find best parameters
            model = auto_arima(
                clean_data,
                start_p=0, start_q=0,
                max_p=5, max_q=5,
                seasonal=False,
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore',
                trace=False
            )
            
            # Safely extract parameters and handle NaN values
            p = int(model.order[0]) if not pd.isna(model.order[0]) else 1
            d = int(model.order[1]) if not pd.isna(model.order[1]) else 1
            q = int(model.order[2]) if not pd.isna(model.order[2]) else 1
            
            # Ensure parameters are non-negative
            p = max(0, p)
            d = max(0, d)
            q = max(0, q)
            
            logger.info(f"ARIMA parameters found: p={p}, d={d}, q={q}")
            return p, d, q
            
        except Exception as e:
            logger.error(f"Error finding ARIMA parameters: {e}")
            # Fallback to simple parameters
            return 1, 1, 1
    
    def calculate_model_metrics(self, actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
        """
        Calculate model evaluation metrics
        """
        # Remove any NaN or infinite values
        mask = np.isfinite(actual) & np.isfinite(predicted)
        actual = actual[mask]
        predicted = predicted[mask]
        
        if len(actual) == 0:
            return {'rmse': float('inf'), 'mae': float('inf'), 'mape': float('inf')}
        
        # Calculate metrics
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        mae = mean_absolute_error(actual, predicted)
        
        # MAPE calculation with handling for zero values
        mape = np.mean(np.abs((actual - predicted) / np.where(actual != 0, actual, 1))) * 100
        
        return {
            'rmse': float(rmse),
            'mae': float(mae),
            'mape': float(mape)
        }
    
    def calculate_acf_pacf(self, data: pd.Series, nlags: int = 20) -> Dict[str, List[float]]:
        """
        Calculate ACF and PACF values
        """
        try:
            acf_values = acf(data.dropna(), nlags=nlags, fft=False)
            pacf_values = pacf(data.dropna(), nlags=nlags)
            
            return {
                'acf': acf_values.tolist(),
                'pacf': pacf_values.tolist()
            }
        except Exception as e:
            logger.error(f"Error calculating ACF/PACF: {e}")
            return {'acf': [], 'pacf': []}
    
    @retry_database_operation(max_retries=3, delay=1)
    def generate_forecast(self, medicine_id: int, forecast_period: str = 'weekly', 
                         forecast_horizon: int = 4) -> DemandForecast:
        """
        Generate demand forecast for a medicine using ARIMA
        """
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            
            # Prepare sales data
            sales_data = self.prepare_sales_data(medicine_id, forecast_period)
            
            min_points = self.min_data_points.get(forecast_period, 30)
            if len(sales_data) < min_points:
                raise ValueError(f"Insufficient {forecast_period} data points. Need at least {min_points}, got {len(sales_data)}")
            
            # Prepare time series data
            ts_data = sales_data.set_index('date')['quantity']
            
            # Clean data - remove NaN and infinite values
            ts_data = ts_data.dropna()
            if len(ts_data) == 0:
                raise ValueError("No valid data points after cleaning NaN values")
            
            # Ensure all values are finite
            ts_data = ts_data[np.isfinite(ts_data)]
            if len(ts_data) == 0:
                raise ValueError("No finite data points available for forecasting")
            
            # Sanitize input data - handle outliers and negative values
            ts_data = ts_data.clip(lower=0)  # Remove negative values
            # Cap extreme outliers at 3 standard deviations
            mean_val = ts_data.mean()
            std_val = ts_data.std()
            if std_val > 0:
                upper_bound = mean_val + 3 * std_val
                ts_data = ts_data.clip(upper=upper_bound)
            
            logger.info(f"Cleaned time series data: {len(ts_data)} points, range: {ts_data.min():.2f} to {ts_data.max():.2f}")
            
            # Find optimal ARIMA parameters
            p, d, q = self.find_optimal_arima_params(ts_data)
            
            # Fit ARIMA model
            from statsmodels.tsa.arima.model import ARIMA
            model = ARIMA(ts_data, order=(p, d, q))
            fitted_model = model.fit()
            
            # Generate forecast
            forecast_result = fitted_model.forecast(steps=forecast_horizon)
            forecast_values = forecast_result.values.tolist()
            
            # Handle NaN values in forecast
            forecast_values = [0.0 if pd.isna(val) or not np.isfinite(val) else float(val) for val in forecast_values]
            
            # Calculate confidence intervals with safer handling
            forecast_object = fitted_model.get_forecast(steps=forecast_horizon)
            conf_int = forecast_object.conf_int()
            lower_bounds = conf_int.iloc[:, 0].astype(float).fillna(0).tolist()
            upper_bounds = conf_int.iloc[:, 1].astype(float).fillna(0).tolist()
            
            confidence_intervals = {
                'lower': lower_bounds,
                'upper': upper_bounds
            }
            
            # Calculate model metrics using in-sample predictions
            fitted_values = fitted_model.fittedvalues
            actual_values = ts_data.iloc[len(ts_data) - len(fitted_values):].values
            
            metrics = self.calculate_model_metrics(actual_values, fitted_values.values)
            
            # Calculate ACF and PACF
            acf_pacf = self.calculate_acf_pacf(ts_data)
            
            # Create DemandForecast object within a transaction
            with transaction.atomic():
                forecast = DemandForecast.objects.create(
                    medicine=medicine,
                    forecast_period=forecast_period,
                    forecast_horizon=forecast_horizon,
                    arima_p=p,
                    arima_d=d,
                    arima_q=q,
                    aic=float(fitted_model.aic),
                    bic=float(fitted_model.bic),
                    rmse=metrics['rmse'],
                    mae=metrics['mae'],
                    mape=metrics['mape'],
                    forecasted_demand=forecast_values,
                    confidence_intervals=confidence_intervals,
                    training_data_start=sales_data['date'].min(),
                    training_data_end=sales_data['date'].max(),
                    training_data_points=len(sales_data)
                )
            
            logger.info(f"Successfully generated forecast for {medicine.name}")
            return forecast
            
        except Exception as e:
            logger.error(f"Error generating forecast for medicine {medicine_id}: {e}")
            raise
    
    def optimize_inventory_levels(self, forecast: DemandForecast, 
                                 service_level: float = 95.0,
                                 lead_time_days: int = 7,
                                 holding_cost_percentage: float = 20.0) -> InventoryOptimization:
        """
        Calculate optimal inventory levels based on demand forecast
        """
        try:
            # Get forecasted demand
            forecasted_demand = np.array(forecast.forecasted_demand)
            
            # Calculate average demand during lead time
            avg_demand_lead_time = np.mean(forecasted_demand) * (lead_time_days / 7)  # assuming weekly forecast
            
            # Calculate demand standard deviation
            demand_std = np.std(forecasted_demand)
            
            # Handle NaN and zero values
            if np.isnan(avg_demand_lead_time) or avg_demand_lead_time <= 0:
                avg_demand_lead_time = 1.0  # Minimum demand
            if np.isnan(demand_std) or demand_std <= 0:
                demand_std = 1.0  # Minimum standard deviation
            
            # Calculate safety stock using service level
            from scipy import stats
            z_score = stats.norm.ppf(service_level / 100)
            safety_stock = z_score * demand_std * np.sqrt(lead_time_days / 7)
            
            # Ensure safety stock is not NaN
            if np.isnan(safety_stock) or safety_stock < 0:
                safety_stock = 1.0
            
            # Calculate reorder point
            reorder_point = int(max(1, avg_demand_lead_time + safety_stock))
            
            # Calculate optimal order quantity using EOQ model
            # EOQ = sqrt(2 * D * S / H)
            # D = annual demand, S = ordering cost, H = holding cost per unit per year
            
            annual_demand = np.sum(forecasted_demand) * (52 / len(forecasted_demand))  # annualize
            
            # Dynamic ordering cost based on medicine category
            category = forecast.medicine.category.name.lower()
            if 'prescription' in category or 'controlled' in category:
                ordering_cost = Decimal('100.0')  # Higher cost for controlled substances
            elif 'vitamin' in category or 'supplement' in category:
                ordering_cost = Decimal('25.0')  # Lower cost for supplements
            elif 'emergency' in category or 'critical' in category:
                ordering_cost = Decimal('75.0')  # Medium-high cost for emergency meds
            else:
                ordering_cost = Decimal('50.0')  # Default cost
            
            holding_cost_per_unit = forecast.medicine.unit_price * Decimal(str(holding_cost_percentage / 100))
            
            # Ensure annual demand is positive
            if annual_demand <= 0 or np.isnan(annual_demand):
                annual_demand = 1.0
            
            eoq = np.sqrt(2 * annual_demand * float(ordering_cost) / float(holding_cost_per_unit))
            
            # Handle NaN or invalid EOQ
            if np.isnan(eoq) or eoq <= 0:
                optimal_order_quantity = 10  # Default minimum order
            else:
                optimal_order_quantity = int(max(1, eoq))
            
            # Calculate maximum stock level
            optimal_maximum_stock = reorder_point + optimal_order_quantity
            
            # Calculate expected costs with NaN handling
            expected_holding_cost = Decimal(str(optimal_order_quantity / 2)) * holding_cost_per_unit
            
            stockout_probability = (1 - service_level / 100)
            expected_stockout_cost = Decimal(str(stockout_probability * annual_demand)) * forecast.medicine.unit_price * Decimal('0.1')  # 10% of unit price as stockout cost
            
            # Ensure costs are not NaN
            if expected_holding_cost.is_nan():
                expected_holding_cost = Decimal('0.0')
            if expected_stockout_cost.is_nan():
                expected_stockout_cost = Decimal('0.0')
                
            total_expected_cost = expected_holding_cost + expected_stockout_cost
            
            # Create InventoryOptimization object
            optimization = InventoryOptimization.objects.create(
                medicine=forecast.medicine,
                demand_forecast=forecast,
                service_level=Decimal(str(service_level)),
                lead_time_days=lead_time_days,
                holding_cost_percentage=Decimal(str(holding_cost_percentage)),
                optimal_reorder_point=int(reorder_point),
                optimal_order_quantity=optimal_order_quantity,
                optimal_maximum_stock=optimal_maximum_stock,
                safety_stock=int(safety_stock),
                expected_holding_cost=expected_holding_cost,
                expected_stockout_cost=expected_stockout_cost,
                total_expected_cost=total_expected_cost
            )
            
            logger.info(f"Successfully optimized inventory levels for {forecast.medicine.name}")
            return optimization
            
        except Exception as e:
            logger.error(f"Error optimizing inventory levels: {e}")
            raise
    
    def generate_bulk_forecasts(self, medicine_ids: List[int], 
                               forecast_period: str = 'weekly',
                               forecast_horizon: int = 4) -> List[DemandForecast]:
        """
        Generate forecasts for multiple medicines
        """
        forecasts = []
        
        for medicine_id in medicine_ids:
            try:
                forecast = self.generate_forecast(medicine_id, forecast_period, forecast_horizon)
                forecasts.append(forecast)
            except Exception as e:
                logger.error(f"Failed to generate forecast for medicine {medicine_id}: {e}")
                continue
        
        return forecasts
    
    def update_sales_trends(self, medicine_id: int, period_type: str = 'weekly'):
        """
        Update sales trends for a medicine
        """
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            
            # Get sales data
            sales_data = self.prepare_sales_data(medicine_id, period_type)
            
            # Calculate trends
            for _, row in sales_data.iterrows():
                # Check if trend already exists
                trend, created = SalesTrend.objects.get_or_create(
                    medicine=medicine,
                    period_type=period_type,
                    period_date=row['date'],
                    defaults={
                        'quantity_sold': row['quantity'],
                        'revenue': row['quantity'] * medicine.unit_price,
                        'average_price': medicine.unit_price
                    }
                )
                
                if not created:
                    # Update existing trend
                    trend.quantity_sold = row['quantity']
                    trend.revenue = row['quantity'] * medicine.unit_price
                    trend.average_price = medicine.unit_price
                    trend.save()
            
            # Calculate growth rates and seasonal factors
            self._calculate_trend_indicators(medicine_id, period_type)
            
        except Exception as e:
            logger.error(f"Error updating sales trends for medicine {medicine_id}: {e}")
            raise
    
    def _calculate_trend_indicators(self, medicine_id: int, period_type: str):
        """
        Calculate growth rates and seasonal factors for sales trends
        """
        trends = SalesTrend.objects.filter(
            medicine_id=medicine_id,
            period_type=period_type
        ).order_by('period_date')
        
        if len(trends) < 2:
            return
        
        # Calculate growth rates
        for i in range(1, len(trends)):
            prev_quantity = trends[i-1].quantity_sold
            curr_quantity = trends[i].quantity_sold
            
            if prev_quantity > 0:
                growth_rate = ((curr_quantity - prev_quantity) / prev_quantity) * 100
                trends[i].growth_rate = growth_rate
                
                # Determine trend direction
                if growth_rate > 5:
                    trends[i].trend_direction = 'up'
                elif growth_rate < -5:
                    trends[i].trend_direction = 'down'
                else:
                    trends[i].trend_direction = 'stable'
                
                trends[i].save()


class SupplyChainOptimizer:
    """
    Supply chain optimization service
    """
    
    def __init__(self):
        self.forecasting_service = ARIMAForecastingService()
    
    def optimize_supply_chain(self, medicine_ids: List[int]) -> Dict[int, InventoryOptimization]:
        """
        Optimize supply chain for multiple medicines
        """
        optimizations = {}
        
        for medicine_id in medicine_ids:
            try:
                # Generate forecast
                forecast = self.forecasting_service.generate_forecast(medicine_id)
                
                # Optimize inventory levels
                optimization = self.forecasting_service.optimize_inventory_levels(forecast)
                
                optimizations[medicine_id] = optimization
                
            except Exception as e:
                logger.error(f"Failed to optimize supply chain for medicine {medicine_id}: {e}")
                continue
        
        return optimizations
    
    def generate_reorder_alerts(self) -> List[Dict]:
        """
        Generate reorder alerts based on current stock levels and forecasts
        """
        alerts = []
        
        # Get all medicines with low stock
        low_stock_medicines = Medicine.objects.filter(
            current_stock__lte=F('reorder_point'),
            is_active=True
        )
        
        for medicine in low_stock_medicines:
            try:
                # Get latest forecast
                latest_forecast = DemandForecast.objects.filter(
                    medicine=medicine,
                    is_active=True
                ).order_by('-created_at').first()
                
                if latest_forecast:
                    # Get latest optimization
                    optimization = InventoryOptimization.objects.filter(
                        demand_forecast=latest_forecast,
                        is_active=True
                    ).first()
                    
                    if optimization:
                        suggested_quantity = optimization.optimal_order_quantity
                        priority = self._calculate_priority(medicine, optimization)
                    else:
                        suggested_quantity = medicine.reorder_point * 2
                        priority = 'medium'
                else:
                    suggested_quantity = medicine.reorder_point * 2
                    priority = 'medium'
                
                alerts.append({
                    'medicine': medicine,
                    'current_stock': medicine.current_stock,
                    'reorder_point': medicine.reorder_point,
                    'suggested_quantity': suggested_quantity,
                    'priority': priority
                })
                
            except Exception as e:
                logger.error(f"Error generating reorder alert for {medicine.name}: {e}")
                continue
        
        return alerts
    
    def _calculate_priority(self, medicine: Medicine, optimization: InventoryOptimization) -> str:
        """
        Calculate priority level for reorder alert
        """
        stock_ratio = medicine.current_stock / optimization.optimal_reorder_point
        
        if stock_ratio <= 0.5:
            return 'urgent'
        elif stock_ratio <= 0.75:
            return 'high'
        elif stock_ratio <= 1.0:
            return 'medium'
        else:
            return 'low'
