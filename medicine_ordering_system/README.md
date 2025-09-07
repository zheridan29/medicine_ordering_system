# OnCare Medicine Ordering System

A comprehensive Web-Based Ordering System with Customer-Centric Supply Chain Analytics for ordering medicine, built with Django and featuring ARIMA-based demand forecasting.

## 🏥 Features

### Core Functionality
- **Multi-Role User Management**: Customer, Pharmacist, and Admin roles
- **Medicine Catalog**: Comprehensive medicine database with detailed information
- **Order Management**: Complete order lifecycle from cart to delivery
- **Prescription Handling**: Digital prescription upload and verification
- **Inventory Management**: Real-time stock tracking and reorder alerts
- **Payment Processing**: Secure payment handling with multiple methods

### Advanced Analytics
- **ARIMA Forecasting**: Auto ARIMA implementation for demand prediction
- **Supply Chain Optimization**: EOQ calculations and optimal reorder points
- **Data Visualization**: Interactive charts and dashboards
- **Performance Metrics**: AIC, BIC, RMSE, MAE, MAPE evaluation
- **Cost Analysis**: Holding costs and stockout cost optimization

### Security & Compliance
- **HIPAA Compliance**: Healthcare data protection
- **GDPR Compliance**: Data privacy and user consent
- **Audit Logging**: Comprehensive activity tracking
- **Role-based Access Control**: Multi-level permissions
- **Security Monitoring**: Real-time threat detection

## 🛠️ Technology Stack

### Backend
- **Django 4.2**: Web framework (MTV pattern)
- **Python 3.8+**: Programming language
- **MariaDB**: Primary database
- **Redis**: Caching and session storage
- **Celery**: Asynchronous task processing

### Frontend
- **Bootstrap 5**: Responsive UI framework
- **Chart.js**: Data visualization
- **jQuery**: Interactive functionality
- **Font Awesome**: Icons

### Analytics & ML
- **Pandas**: Data manipulation
- **NumPy**: Numerical computing
- **Statsmodels**: Statistical modeling
- **PMDARIMA**: Auto ARIMA implementation
- **Scikit-learn**: Machine learning utilities

## 📋 Prerequisites

- Python 3.8 or higher
- MariaDB 10.3 or higher
- Redis 6.0 or higher
- Node.js (for frontend assets)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd medicine_ordering_system
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
# Create MariaDB database
mysql -u root -p
CREATE DATABASE medicine_ordering_db;
GRANT ALL PRIVILEGES ON medicine_ordering_db.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Environment Configuration
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_NAME=medicine_ordering_db
DATABASE_USER=your_user
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=3306
REDIS_URL=redis://localhost:6379
```

### 6. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Load Sample Data (Optional)
```bash
python manage.py loaddata sample_data.json
```

### 9. Run Development Server
```bash
python manage.py runserver
```

## 📁 Project Structure

```
medicine_ordering_system/
├── accounts/                 # User authentication & management
├── analytics/               # ARIMA forecasting & analytics
├── audits/                  # Activity logs & security monitoring
├── common/                  # Shared utilities & helpers
├── inventory/               # Medicine catalog & stock management
├── oncare_admin/           # Admin dashboards & reporting
├── orders/                 # Order placement & tracking
├── transactions/           # Payments & sales transactions
├── templates/              # HTML templates
├── static/                 # CSS, JS, and media files
├── media/                  # User uploaded files
├── requirements.txt        # Python dependencies
├── manage.py              # Django management script
└── README.md              # This file
```

## 🔧 Configuration

### Database Configuration
Update `settings.py` for your database configuration:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'medicine_ordering_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Redis Configuration
For production, update Redis settings:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

## 📊 Usage

### 1. Admin Dashboard
- Access: `/oncare-admin/`
- Features: System monitoring, user management, reports

### 2. Analytics Dashboard
- Access: `/analytics/`
- Features: Demand forecasting, inventory optimization, visualizations

### 3. Inventory Management
- Access: `/inventory/`
- Features: Medicine catalog, stock management, reorder alerts

### 4. Order Management
- Access: `/orders/`
- Features: Order processing, cart management, prescription handling

### 5. API Endpoints
- Base URL: `/api/`
- Documentation: Available at `/api/docs/` (when implemented)

## 🔍 ARIMA Forecasting

### Generate Forecast
```python
from analytics.services import ARIMAForecastingService

service = ARIMAForecastingService()
forecast = service.generate_forecast(
    medicine_id=1,
    forecast_period='weekly',
    forecast_horizon=4
)
```

### Optimize Inventory
```python
optimization = service.optimize_inventory_levels(
    forecast=forecast,
    service_level=95.0,
    lead_time_days=7
)
```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Run Specific App Tests
```bash
python manage.py test analytics
python manage.py test inventory
```

### Coverage Report
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🚀 Deployment

### Production Settings
1. Set `DEBUG = False`
2. Configure production database
3. Set up Redis for caching
4. Configure static file serving
5. Set up SSL certificates
6. Configure email settings

### Docker Deployment
```bash
docker-compose up -d
```

### Environment Variables
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=mysql://user:password@host:port/database
REDIS_URL=redis://host:port
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 📈 Performance Optimization

### Database Optimization
- Use database indexes for frequently queried fields
- Implement database connection pooling
- Use `select_related` and `prefetch_related` for ORM queries

### Caching Strategy
- Cache frequently accessed data in Redis
- Use template fragment caching
- Implement API response caching

### ARIMA Optimization
- Use background tasks for heavy forecasting operations
- Implement result caching for repeated forecasts
- Optimize data preprocessing for large datasets

## 🔒 Security

### Authentication
- Multi-factor authentication support
- Session-based authentication with Redis
- Password strength validation

### Authorization
- Role-based access control (RBAC)
- Permission-based view access
- API token authentication

### Data Protection
- HTTPS enforcement
- Input validation and sanitization
- SQL injection prevention
- XSS protection

## 📝 API Documentation

### Authentication Endpoints
- `POST /accounts/api/login/` - User login
- `POST /accounts/api/logout/` - User logout
- `POST /accounts/api/register/` - User registration

### Inventory Endpoints
- `GET /inventory/api/medicines/` - List medicines
- `POST /inventory/api/stock-movements/` - Add stock movement
- `GET /inventory/api/reorder-alerts/` - Get reorder alerts

### Analytics Endpoints
- `POST /analytics/api/forecast/generate/` - Generate forecast
- `GET /analytics/api/sales-trends/{id}/` - Get sales trends
- `GET /analytics/api/inventory-optimization/{id}/` - Get optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Core ordering functionality
- ARIMA forecasting implementation
- Multi-role user management
- Comprehensive audit logging

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [ARIMA Forecasting Guide](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima_model.ARIMA.html)

---

**Built with ❤️ for better healthcare supply chain management**


