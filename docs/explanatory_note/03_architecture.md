# Пояснительная записка: SportHub
## Часть 3: Архитектура проекта

---

## 1. Структура файлов проекта

```
SportHub/
├── db.sqlite3                    # База данных (SQLite для разработки)
├── manage.py                     # CLI для управления Django приложением
├── requirements.txt              # Зависимости проекта
├── docs/                         # Документация
│   └── explanatory_note/         # Пояснительная записка
├── media/                        # Загруженные пользователями файлы
│   └── products/                 # Изображения товаров
├── static/                       # Статические файлы
│   └── css/
│       └── style.css             # Стили приложения
├── sporthub/                     # Главное приложение Django
│   ├── __init__.py
│   ├── settings.py               # Конфигурация проекта
│   ├── urls.py                   # Главная таблица маршрутов
│   ├── wsgi.py                   # WSGI интерфейс для веб-серверов
│   └── __pycache__/
└── store/                        # Основное приложение (app)
    ├── migrations/               # Версионирование схемы БД
    ├── templates/
    │   └── store/
    │       ├── base.html         # Базовый шаблон
    │       ├── home.html         # Главная страница
    │       ├── catalog.html      # Каталог товаров
    │       ├── product_detail.html
    │       ├── cart.html         # Корзина покупок
    │       ├── checkout.html     # Оформление заказа
    │       ├── order_detail.html # Детали заказа
    │       ├── my_orders.html    # История заказов
    │       ├── account.html      # Управление профилем
    │       ├── login.html        # Форма входа
    │       ├── register.html     # Форма регистрации
    │       └── partials/
    │           └── product_card.html
    ├── management/
    │   └── commands/
    │       ├── __init__.py
    │       └── seed_data.py      # Команда заполнения тестовых данных
    ├── __init__.py
    ├── admin.py                  # Конфигурация Django Admin
    ├── apps.py                   # Конфигурация приложения
    ├── context_processors.py     # Глобальные переменные для шаблонов
    ├── models.py                 # Определение моделей данных
    ├── urls.py                   # Таблица маршрутов приложения
    ├── views.py                  # Представления (контроллеры)
    └── __pycache__/
```

---

## 2. Архитектурная парадигма: MTV (Model-Template-View)

Проект следует архитектурной парадигме Django MTV, которая является модификацией классической MVC:

```
┌─────────────────────────────────────────────────────┐
│                   User Request                       │
│                   (Browser)                          │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              urls.py (URL Routing)                  │
│        Маршрутизирует URL на View функции           │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              views.py (View Layer)                  │
│     Обрабатывает логику запроса, работает с         │
│     Models для получения/сохранения данных          │
└─────────────────────────────────────────────────────┘
                    │                │
           ┌────────▼──────────┬─────▼──────────┐
           │                  │                │
           ▼                  ▼                ▼
      ┌─────────┐      ┌─────────┐      ┌──────────┐
      │ Models  │      │Templates│      │Context   │
      │(Database│      │(HTML)   │      │Processors│
      │Queries) │      │         │      │(Variables│
      └─────────┘      └─────────┘      └──────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  HTML Response  │
                    │  (Browser)      │
                    └─────────────────┘
```

### 2.1 Model (Модель)

Определяет структуру данных и содержит бизнес-логику:

```python
# models.py
class Product(models.Model):
    category = models.ForeignKey(Category, ...)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    
    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int((1 - self.price / self.old_price) * 100)
        return None
```

### 2.2 Template (Шаблон)

Отвечает за отображение данных в HTML:

```django
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>...</head>
<body>
  <nav class="navbar">...</nav>
  {% block content %}
    <!-- Подматериалы переопределяют этот блок -->
  {% endblock %}
  <footer>...</footer>
</body>
</html>
```

### 2.3 View (Представление)

Отвечает за обработку логики запроса:

```python
# views.py
@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})
```

---

## 3. Логика взаимодействия компонентов

### 3.1 Процесс покупки товара (общий поток)

```
Пользователь нажимает
"Добавить в корзину"
        │
        ▼
   URL: /cart/add/<product_id>/
        │
        ▼
   add_to_cart() View
   │   ├─ Получить Product из БД
   │   ├─ Получить или создать Cart пользователя
   │   ├─ Получить или создать CartItem
   │   ├─ Увеличить quantity если товар уже есть
   │   └─ Сохранить в БД
        │
        ▼
   Перенаправить на предыдущую страницу
        │
        ▼
Кэш cart_count обновляется
```

### 3.2 Процесс оформления заказа

```
Пользователь заполняет форму
(адрес, телефон) и нажимает
"Оформить заказ"
        │
        ▼
   POST /checkout/
        │
        ▼
   checkout() View
   │   ├─ Получить Cart пользователя
   │   ├─ Валидировать поля формы
   │   ├─ Создать Order в БД
   │   ├─ Для каждого CartItem:
   │   │   ├─ Создать OrderItem
   │   │   └─ Уменьшить Product.stock на quantity
   │   ├─ Очистить CartItem (удалить)
   │   └─ Перенаправить на страницу заказа
        │
        ▼
   order_detail() View
   (отображение заказа)
```

### 3.3 Система аудентификации

```
┌──────────────────────────────────┐
│   Неавторизованный пользователь  │
└──────────────────────────────────┘
            │         │
      ┌─────▼─┐    ┌──▼──────┐
      │ Login │    │Register │
      └─────┬─┘    └──┬──────┘
            │         │
      ┌─────▼─────────▼──┐
      │  create User     │
      │  Django auth     │
      └─────┬────────────┘
            │
      ┌─────▼──────────────┐
      │ create Cart        │
      │ (signal handler)   │
      └─────┬──────────────┘
            │
      ┌─────▼─────────────────┐
      │ Авторизованный user   │
      │ Доступ к корзине,     │
      │ заказам, профилю      │
      └───────────────────────┘
```

---

## 4. Модели данных и их связи

### 4.1 Диаграмма Entity-Relationship (ER)

```
┌──────────────┐
│   Category   │
├──────────────┤
│ - name       │◄──────────┐
│ - slug       │           │ 1:N
│ - icon       │           │
└──────────────┘           │
                           │
                    ┌──────┴──────┐
                    │   Product   │
                    ├─────────────┤
                    │ - name      │
                    │ - price     │
                    │ - stock     │
                    │ - image     │
                    │ - category  │(FK)
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         │                 │                 │
      1:N             1:N               1:N
         │                 │                 │
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐      ┌──────────┐     ┌─────────────┐
    │CartItem │──┐   │OrderItem │     │   ...cart   │
    ├─────────┤  │   ├──────────┤     └─────────────┘
    │ - qty   │  │   │ - qty    │
    │ - cart  │  │   │ - price  │
    │ - prod  │  │   │ - order  │
    └────┬────┘  │   │ - prod   │
         │       │   └────┬─────┘
         │       │        │
         │       │        │
    ┌────▼───────▼┐  ┌────▼──────┐
    │    Cart     │  │   Order   │
    ├────────────┤  ├───────────┤
    │ - user (1:1)  │ - user (1:N)
    │ - created_at  │ - status
    │ - items(1:N)  │ - address
    └────┬─────────┘ │ - phone
         │           │ - total
         │           └───────────┘
    ┌────▼────────────┐
    │       User      │
    │  (Django Auth)  │
    ├─────────────────┤
    │ - username      │
    │ - email         │
    │ - password      │
    │ - ...           │
    └─────────────────┘
```

### 4.2 Ключевые отношения

| Модель A | Тип | Модель B | Описание |
|----------|------|----------|----------|
| Category | 1:N | Product | Каждая категория содержит множество товаров |
| Product | 1:N | CartItem | Один товар может быть в корзине много раз (у разных пользователей) |
| Cart | 1:N | CartItem | Корзина содержит множество товаров |
| User | 1:1 | Cart | Каждый пользователь имеет одну корзину |
| User | 1:N | Order | Пользователь может иметь множество заказов |
| Order | 1:N | OrderItem | Заказ содержит множество товаров |
| Product | 1:N | OrderItem | Один товар может быть в многих заказах |

---

## 5. Система управления сессией пользователя

```
┌──────────────┐
│   Middleware │ (session, auth, csrf)
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│  request.user populated  │
│  with current user info  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│   View Function          │
│   Can access:            │
│   - request.user         │
│   - request.user.is_auth │
│   - request.user.cart    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│   Context Processor      │  (cart_count)
│   Добавляет в контекст:  │
│   - cart_count           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│   Template               │
│   Использует переменные  │
│   - user, cart_count     │
└──────────────────────────┘
```

---

## 6. Поток данных при HTTP запросе

```
1. Browser отправляет HTTP GET /catalog/
                         │
2. Django middleware     │
   обрабатывает запрос   │
                         │
3. urls.py находит       │
   подходящий паттерн     │
   и вызывает view        │
            │
            ▼
4. catalog() получает
   все товары из БД
   и фильтрует их
            │
            ▼
5. cart_count()
   context processor
   добавляет cart_count
   в контекст
            │
            ▼
6. Django рендерит
   шаблон catalog.html
   с контекстом
            │
            ▼
7. HTML отправляется
   в browser
            │
            ▼
8. Browser отображает
   страницу с товарами
```

---

## 7. Оптимизация производительности на архитектурном уровне

### 7.1 N+1 Prevention (Предотвращение проблемы N+1)

**До оптимизации:**
```python
products = Product.objects.all()
for product in products:
    print(product.category.name)  # N SQL запросов!
```

**После оптимизации:**
```python
products = Product.objects.select_related('category')
for product in products:
    print(product.category.name)  # 1 SQL запрос!
```

### 7.2 Кэширование на уровне контекст-процессора

```python
def cart_count(request):
    cache_key = f'cart_count_{request.user.id}'
    cart_count_value = cache.get(cache_key)
    
    if cart_count_value is None:
        cart_count_value = calculate_count()
        cache.set(cache_key, cart_count_value, 300)
    
    return {'cart_count': cart_count_value}
```

### 7.3 Использование F() expressions для БД операций

```python
# Вместо Python цикла:
for item in items:
    product = item.product
    product.stock -= item.quantity
    product.save()  # N SQL updates

# Используется SQL update:
Product.objects.filter(id__in=ids).update(
    stock=F('stock') - qty
)  # 1 SQL update
```

---

## 8. Безопасность архитектуры

### 8.1 CSRF Protection

Все POST формы включают CSRF токен:
```django
<form method="POST">
    {% csrf_token %}
    <!-- Form fields -->
</form>
```

### 8.2 SQL Injection Protection

Django ORM использует параметризованные запросы:
```python
# Безопасно (параметризовано):
Product.objects.filter(name__icontains=user_input)

# Опасно (не использовать):
Product.objects.raw(f"SELECT * FROM product WHERE name = '{user_input}'")
```

### 8.3 Аутентификация и авторизация

```python
@login_required  # Только авторизованные пользователи
def cart_view(request):
    cart = Cart.objects.get(user=request.user)
    return render(request, 'store/cart.html', {'cart': cart})
```

---

## Итоговая архитектурная схема

```
┌─────────────────────────────────────────────────────┐
│               Internet / Browser                    │
└────────────────────┬────────────────────────────────┘
                     │ HTTP Request/Response
                     ▼
┌─────────────────────────────────────────────────────┐
│           Django WSGI Application                   │
├─────────────────────────────────────────────────────┤
│  ┌──────────────┐                                   │
│  │ Middleware   │ (Session, Auth, CSRF, Cache)     │
│  └──────┬───────┘                                   │
│         │                                            │
│  ┌──────▼──────────┐                                │
│  │  URL Router    │                                 │
│  │  urls.py       │                                 │
│  └──────┬──────────┘                                │
│         │                                            │
│  ┌──────▼──────────────────┐                        │
│  │    VIEW LAYER           │                        │
│  │    views.py             │                        │
│  │  Multiple functions     │                        │
│  └──────┬───────────────────┘                       │
│         │                                            │
│    ┌────┴────────────┬──────────────┬──────────────┐│
│    │                 │              │              ││
│  ┌─▼────────┐  ┌────▼────┐  ┌────▼──────┐  ┌───▼──┐│
│  │  MODELS  │  │TEMPLATES│  │ CACHE     │  │ ORM  ││
│  │ models.py   │ *.html  │  │ (Redis)   │  │Query ││
│  └─┬────────┘  └────┬────┘  └────┬──────┘  └───┬──┘│
│    │                 │            │             │    │
└────┼─────────────────┼────────────┼─────────────┼────┘
     │                 │            │             │
     ▼                 ▼            ▼             ▼
  ┌─────────────────────────────────────────────────┐
  │               DATA LAYER                        │
  ├─────────────────────────────────────────────────┤
  │  Database (PostgreSQL / SQLite)                │
  │  - Таблицы для всех моделей                   │
  │  - Индексы для оптимизации запросов           │
  │  - Миграции для версионирования схемы         │
  └─────────────────────────────────────────────────┘
```

---

**Версия документа:** 1.0  
**Дата обновления:** 6 апреля 2026 г.
