"""
ARIMA forecasting service for demand prediction and supply chain optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

from pmdarima import auto_arima
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.tsa.seasonal import seasonal_decompose
from sklearn.metrics import mean_squared_error, mean_absolute_error
import warnings

from django.db.models import Sum, Count, Q
from django.utils import timezone

from .models import DemandForecast, InventoryOptimization, SalesTrend
from inventory.models import Medicine
from orders.models import OrderItem
from transactions.models import Transaction

logger = logging.getLogger(__name__)
warnings.filterwarnings('ignore')


class ARIMAForecastingService:
    """
    Service class for ARIMA-based demand forecasting
    """
    
    def __init__(self):
        self.min_data_points = 30  # Minimum data points required for forecasting
        
    def prepare_sales_data(self, medicine_id: int, period_type: str = 'daily', 
                          start_date: Optional[datetime] = None, 
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Prepare sales data for ARIMA forecasting
        """
        if not start_date:
            start_date = timezone.now() - timedelta(days=365)
        if not end_date:
            end_date = timezone.now()
            
        # Get sales data from OrderItems
        order_items = OrderItem.objects.filter(
            medicine_id=medicine_id,
            order__created_at__range=[start_date, end_date],
            order__status__in=['confirmed', 'processing', 'shipped', 'delivered']
        ).values('order__created_at', 'quantity').order_by('order__created_at')
        
        if not order_items:
            raise ValueError(f"No sales data found for medicine {medicine_id}")
        
        # Convert to DataFrame
        df = pd.DataFrame(list(order_items))
        df['order__created_at'] = pd.to_datetime(df['order__created_at'])
        
        # Group by period
        if period_type == 'daily':
            df = df.groupby(df['order__created_at'].dt.date)['quantity'].sum().reset_index()
            df.columns = ['date', 'quantity']
        elif period_type == 'weekly':
            df['week'] = df['order__created_at'].dt.to_period('W')
            df = df.groupby('week')['quantity'].sum().reset_index()
            df['date'] = df['week'].dt.start_time.dt.date
            df = df[['date', 'quantity']]
        elif period_type == 'monthly':
            df['month'] = df['order__created_at'].dt.to_period('M')
            df = df.groupby('month')['quantity'].sum().reset_index()
            df['date'] = df['month'].dt.start_time.dt.date
            df = df[['date', 'quantity']]
        else:
            raise ValueError("period_type must be 'daily', 'weekly', or 'monthly'")
        
        # Fill missing dates with 0
        date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D' if period_type == 'daily' else 'W' if period_type == 'weekly' else 'M')
        df = df.set_index('date').reindex(date_range.date, fill_value=0).reset_index()
        df.columns = ['date', 'quantity']
        
        return df
    
    def find_optimal_arima_params(self, data: pd.Series) -> Tuple[int, int, int]:
        """
        Find optimal ARIMA parameters using auto_arima
        """
        try:
            # Use auto_arima to find best parameters
            model = auto_arima(
                data,
                start_p=0, start_q=0,
                max_p=5, max_q=5,
                seasonal=False,
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore',
                trace=False
            )
            
            return model.order[0], model.order[1], model.order[2]  # p, d, q
            
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
    
    def generate_forecast(self, medicine_id: int, forecast_period: str = 'weekly', 
                         forecast_horizon: int = 4) -> DemandForecast:
        """
        Generate demand forecast for a medicine using ARIMA
        """
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            
            # Prepare sales data
            sales_data = self.prepare_sales_data(medicine_id, forecast_period)
            
            if len(sales_data) < self.min_data_points:
                raise ValueError(f"Insufficient data points. Need at least {self.min_data_points}, got {len(sales_data)}")
            
            # Prepare time series data
            ts_data = sales_data.set_index('date')['quantity']
            
            # Find optimal ARIMA parameters
            p, d, q = self.find_optimal_arima_params(ts_data)
            
            # Fit ARIMA model
            from statsmodels.tsa.arima.model import ARIMA
            model = ARIMA(ts_data, order=(p, d, q))
            fitted_model = model.fit()
            
            # Generate forecast
            forecast_result = fitted_model.forecast(steps=forecast_horizon)
            forecast_values = forecast_result.values.tolist()
            
            # Calculate confidence intervals
            conf_int = fitted_model.get_forecast(steps=forecast_horizon).conf_int()
            confidence_intervals = {
                'lower': conf_int.iloc[:, 0].values.tolist(),
                'upper': conf_int.iloc[:, 1].values.tolist()
            }
            
            # Calculate model metrics using in-sample predictions
            fitted_values = fitted_model.fittedvalues
            actual_values = ts_data.iloc[len(ts_data) - len(fitted_values):].values
            
            metrics = self.calculate_model_metrics(actual_values, fitted_values.values)
            
            # Calculate ACF and PACF
            acf_pacf = self.calculate_acf_pacf(ts_data)
            
            # Create DemandForecast object
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
            
            # Calculate safety stock using service level
            from scipy import stats
            z_score = stats.norm.ppf(service_level / 100)
            safety_stock = z_score * demand_std * np.sqrt(lead_time_days / 7)
            
            # Calculate reorder point
            reorder_point = int(avg_demand_lead_time + safety_stock)
            
            # Calculate optimal order quantity using EOQ model
            # EOQ = sqrt(2 * D * S / H)
            # D = annual demand, S = ordering cost, H = holding cost per unit per year
            
            annual_demand = np.sum(forecasted_demand) * (52 / len(forecasted_demand))  # annualize
            ordering_cost = 50.0  # assumed ordering cost
            holding_cost_per_unit = forecast.medicine.unit_price * (holding_cost_percentage / 100)
            
            eoq = np.sqrt(2 * annual_demand * ordering_cost / holding_cost_per_unit)
            optimal_order_quantity = int(eoq)
            
            # Calculate maximum stock level
            optimal_maximum_stock = reorder_point + optimal_order_quantity
            
            # Calculate expected costs
            expected_holding_cost = (optimal_order_quantity / 2) * holding_cost_per_unit
            expected_stockout_cost = (1 - service_level / 100) * annual_demand * forecast.medicine.unit_price * 0.1  # 10% of unit price as stockout cost
            total_expected_cost = expected_holding_cost + expected_stockout_cost
            
            # Create InventoryOptimization object
            optimization = InventoryOptimization.objects.create(
                medicine=forecast.medicine,
                demand_forecast=forecast,
                service_level=service_level,
                lead_time_days=lead_time_days,
                holding_cost_percentage=holding_cost_percentage,
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
            current_stock__lte=models.F('reorder_point'),
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
