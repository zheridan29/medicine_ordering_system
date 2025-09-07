# Deployment Guide - OnCare Medicine Ordering System

## 🚀 Production Deployment

This guide covers deploying the OnCare Medicine Ordering System to production environments.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **RAM**: Minimum 4GB, Recommended 8GB+
- **CPU**: Minimum 2 cores, Recommended 4+ cores
- **Storage**: Minimum 50GB SSD
- **Python**: 3.8 or higher
- **MariaDB**: 10.3 or higher
- **Redis**: 6.0 or higher
- **Nginx**: 1.18 or higher

### Software Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev
sudo apt install mariadb-server redis-server nginx
sudo apt install build-essential libssl-dev libffi-dev

# CentOS/RHEL
sudo yum update
sudo yum install python38 python38-devel
sudo yum install mariadb-server redis nginx
sudo yum groupinstall "Development Tools"
```

## 🐳 Docker Deployment (Recommended)

### 1. Create Dockerfile
```dockerfile
FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "medicine_ordering_system.wsgi:application"]
```

### 2. Create docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=mysql://root:password@db:3306/medicine_ordering_db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./media:/app/media
      - ./static:/app/static

  db:
    image: mariadb:10.6
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=medicine_ordering_db
    volumes:
      - db_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:6.2-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/app/static
      - ./media:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  db_data:
```

### 3. Deploy with Docker
```bash
# Build and start services
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## 🖥️ Manual Deployment

### 1. Server Setup
```bash
# Create application user
sudo useradd -m -s /bin/bash oncare
sudo usermod -aG sudo oncare

# Switch to application user
sudo su - oncare
```

### 2. Application Setup
```bash
# Clone repository
git clone <repository-url> /home/oncare/medicine_ordering_system
cd /home/oncare/medicine_ordering_system

# Create virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration
```bash
# Create database
sudo mysql -u root -p
CREATE DATABASE medicine_ordering_db;
CREATE USER 'oncare_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON medicine_ordering_db.* TO 'oncare_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Environment Configuration
```bash
# Create production settings
cp medicine_ordering_system/settings.py medicine_ordering_system/settings_production.py
```

Update `settings_production.py`:
```python
import os
from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'medicine_ordering_db',
        'USER': 'oncare_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# Security
SECRET_KEY = os.environ.get('SECRET_KEY')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = '/home/oncare/medicine_ordering_system/staticfiles'
MEDIA_ROOT = '/home/oncare/medicine_ordering_system/media'

# Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
```

### 5. Database Migration
```bash
# Set production settings
export DJANGO_SETTINGS_MODULE=medicine_ordering_system.settings_production

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 6. Gunicorn Configuration
Create `/home/oncare/medicine_ordering_system/gunicorn.conf.py`:
```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

### 7. Systemd Service
Create `/etc/systemd/system/oncare.service`:
```ini
[Unit]
Description=OnCare Medicine Ordering System
After=network.target

[Service]
Type=notify
User=oncare
Group=oncare
WorkingDirectory=/home/oncare/medicine_ordering_system
Environment=DJANGO_SETTINGS_MODULE=medicine_ordering_system.settings_production
ExecStart=/home/oncare/medicine_ordering_system/venv/bin/gunicorn --config gunicorn.conf.py medicine_ordering_system.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 8. Nginx Configuration
Create `/etc/nginx/sites-available/oncare`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/oncare/medicine_ordering_system/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/oncare/medicine_ordering_system/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 9. SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 10. Start Services
```bash
# Enable and start services
sudo systemctl enable oncare
sudo systemctl start oncare
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl enable redis
sudo systemctl start redis
sudo systemctl enable mariadb
sudo systemctl start mariadb
```

## 🔧 Production Configuration

### Environment Variables
Create `/home/oncare/.env`:
```env
SECRET_KEY=your-super-secret-key-here
DEBUG=False
DATABASE_URL=mysql://oncare_user:secure_password@localhost:3306/medicine_ordering_db
REDIS_URL=redis://localhost:6379
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Celery Worker Setup
Create `/etc/systemd/system/oncare-celery.service`:
```ini
[Unit]
Description=OnCare Celery Worker
After=network.target

[Service]
Type=forking
User=oncare
Group=oncare
WorkingDirectory=/home/oncare/medicine_ordering_system
Environment=DJANGO_SETTINGS_MODULE=medicine_ordering_system.settings_production
ExecStart=/home/oncare/medicine_ordering_system/venv/bin/celery -A medicine_ordering_system worker --loglevel=info --pidfile=/tmp/celery.pid --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Monitoring Setup
Install monitoring tools:
```bash
# Install htop for system monitoring
sudo apt install htop

# Install log monitoring
sudo apt install logrotate

# Configure log rotation
sudo nano /etc/logrotate.d/oncare
```

Add to `/etc/logrotate.d/oncare`:
```
/home/oncare/medicine_ordering_system/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 oncare oncare
}
```

## 🔍 Health Checks

### Application Health
```bash
# Check application status
curl -f http://localhost:8000/health/ || echo "Application is down"

# Check database connection
python manage.py check --database default

# Check Redis connection
python manage.py shell -c "from django.core.cache import cache; cache.set('test', 'value'); print(cache.get('test'))"
```

### System Health
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep gunicorn
ps aux | grep celery
ps aux | grep nginx
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check MariaDB status
   sudo systemctl status mariadb
   
   # Check database permissions
   mysql -u oncare_user -p -e "SHOW DATABASES;"
   ```

2. **Static Files Not Loading**
   ```bash
   # Collect static files
   python manage.py collectstatic --noinput
   
   # Check Nginx configuration
   sudo nginx -t
   ```

3. **Celery Worker Not Running**
   ```bash
   # Check Celery status
   sudo systemctl status oncare-celery
   
   # Check Redis connection
   redis-cli ping
   ```

4. **SSL Certificate Issues**
   ```bash
   # Test SSL configuration
   openssl s_client -connect yourdomain.com:443
   
   # Renew certificate
   sudo certbot renew
   ```

### Log Files
- Application logs: `/home/oncare/medicine_ordering_system/logs/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`
- MariaDB logs: `/var/log/mysql/`

## 📊 Performance Monitoring

### Application Metrics
```bash
# Monitor Gunicorn processes
ps aux | grep gunicorn

# Monitor memory usage
free -h

# Monitor disk I/O
iostat -x 1
```

### Database Monitoring
```sql
-- Check database size
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'medicine_ordering_db'
GROUP BY table_schema;

-- Check slow queries
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
```

## 🔄 Backup and Recovery

### Database Backup
```bash
# Create backup script
cat > /home/oncare/backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/oncare/backups"
mkdir -p $BACKUP_DIR

mysqldump -u oncare_user -p medicine_ordering_db > $BACKUP_DIR/db_backup_$DATE.sql
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /home/oncare/backup_db.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/oncare/backup_db.sh
```

### Media Files Backup
```bash
# Backup media files
rsync -av /home/oncare/medicine_ordering_system/media/ /backup/media/
```

## 🎯 Scaling Considerations

### Horizontal Scaling
- Use load balancer (HAProxy/Nginx)
- Multiple application servers
- Database read replicas
- Redis cluster

### Vertical Scaling
- Increase server resources
- Optimize database queries
- Implement caching strategies
- Use CDN for static files

---

**Deployment completed successfully! 🎉**

For additional support, refer to the troubleshooting section or contact the development team.


