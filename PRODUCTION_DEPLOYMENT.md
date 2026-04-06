# 🚀 Production Deployment Guide

## 📋 Перед запуском в production

### 1. **Переменные окружения**
Создайте `.env` файл:
```bash
DEBUG=False
SECRET_KEY=your-long-random-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost/sporthub
REDIS_URL=redis://localhost:6379/1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 2. **Переключитесь на PostgreSQL**
SQLite работает для dev, но для production нужна PostgreSQL:

```bash
pip install psycopg2-binary
```

Обновите `settings.py`:
```python
import os
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:password@localhost/sporthub',
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

### 3. **Переключитесь на Redis для кэша**

```bash
pip install django-redis
```

Обновите `settings.py`:
```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 4. **Установите production web server**

```bash
pip install gunicorn whitenoise
```

Создайте `gunicorn_config.py`:
```python
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
```

### 5. **Настройте Security Settings**

В `settings.py`:
```python
# Production security
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
```

### 6. **Настройте Static & Media files**

Установите WhiteNoise для раздачи static:
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Добавьте это
    ...
]

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 7. **Логирование в production**

В `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/sporthub.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

---

## 🚀 Запуск на production

### С помощью systemd (рекомендуется)

Создайте `/etc/systemd/system/sporthub.service`:
```ini
[Unit]
Description=SportHub Django Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/home/sporthub/SportHub
Environment="PATH=/home/sporthub/SportHub/venv/bin"
ExecStart=/home/sporthub/SportHub/venv/bin/gunicorn -c gunicorn_config.py sporthub.wsgi

[Install]
WantedBy=multi-user.target
```

Запустите:
```bash
sudo systemctl enable sporthub
sudo systemctl start sporthub
sudo systemctl status sporthub
```

### Nginx reverse proxy

Создайте `/etc/nginx/sites-available/sporthub`:
```nginx
upstream sporthub {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates (используйте Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://sporthub;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /home/sporthub/SportHub/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias /home/sporthub/SportHub/media/;
        expires 7d;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/sporthub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📊 Мониторинг

### Установите django-silk для отслеживания запросов
```bash
pip install django-silk
```

В `settings.py`:
```python
INSTALLED_APPS = [
    ...
    'silk',
]

MIDDLEWARE = [
    'silk.middleware.SilkyMiddleware',
    ...
]
```

В `urls.py`:
```python
path('silk/', include('silk.urls', namespace='silk')),
```

Доступно на: `https://yourdomain.com/silk/`

---

## 🔒 SSL/TLS с Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com
```

Auto renewal:
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## 📈 Оптимизация базы данных

### Создайте индексы для search:
```sql
CREATE INDEX idx_product_name ON store_product (name);
CREATE INDEX idx_product_category_id ON store_product (category_id);
CREATE INDEX idx_product_is_featured ON store_product (is_featured);
CREATE INDEX idx_order_user_id ON store_order (user_id);
```

### Бэкап БД:
```bash
# Daily backup
pg_dump sporthub > /backups/sporthub_$(date +%Y%m%d_%H%M%S).sql

# Или автоматический через cron:
0 2 * * * pg_dump sporthub | gzip > /backups/sporthub_$(date +\%Y\%m\%d).sql.gz
```

---

## 🚨 Чек-лист before go-live

- [ ] DEBUG = False в settings.py
- [ ] SECRET_KEY изменён на новый длинный ключ
- [ ] ALLOWED_HOSTS правильно установлены
- [ ] База данных = PostgreSQL (не SQLite)
- [ ] Кэш = Redis (не LocMemCache)
- [ ] SSL/TLS сертификат установлен (Let's Encrypt)
- [ ] Gunicorn + Nginx настроены
- [ ] CORS правильно настроены (если требуется)
- [ ] CSRF protection включена
- [ ] Email backend настроен для отправки писем
- [ ] Логирование настроено
- [ ] Бэкап БД настроен
- [ ] Мониторинг (django-silk, Sentry) настроен
- [ ] Все миграции выполнены: `python manage.py migrate`
- [ ] Static files собраны: `python manage.py collectstatic`
- [ ] Тесты пройдены: `python manage.py test`

---

## 🆘 Troubleshooting

### 500 ошибка
Проверьте логи:
```bash
sudo tail -f /var/log/django/sporthub.log
sudo journalctl -u sporthub -f
```

### Медленные запросы
Используйте django-silk на `/silk/` для анализа

### Out of memory
Увеличьте swap или оптимизируйте запросы (используйте select_for_update, prefetc_related)

### Высокая CPU
Используйте `top`, `htop` для мониторинга. Может потребоваться больше workers в gunicorn.

---

**Happy deploying! 🎉**
