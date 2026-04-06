# 📋 Гайдлайны разработки SportHub

## ⚡ Правила написания оптимального кода

### 1. **Никогда не используйте N+1 запросы**

❌ **Плохо:**
```python
products = Product.objects.all()
for product in products:
    print(product.category.name)  # N+1 запрос!
```

✅ **Хорошо:**
```python
products = Product.objects.select_related('category')
for product in products:
    print(product.category.name)  # Один запрос!
```

---

### 2. **Используйте select_related() для ForeignKey**
```python
# Всегда:
Product.objects.select_related('category')
Order.objects.select_related('user')
CartItem.objects.select_related('product', 'product__category')
```

---

### 3. **Используйте prefetch_related() для reverse relations**
```python
# Всегда:
orders = Order.objects.prefetch_related('items', 'items__product')
carts = Cart.objects.prefetch_related('items', 'items__product')
categories = Category.objects.prefetch_related('products')
```

---

### 4. **Используйте F() для операций в БД**

❌ **Плохо:**
```python
for item in cart.items.all():
    product = item.product
    product.stock -= item.quantity
    product.save()  # Цикл по товарам!
```

✅ **Хорошо:**
```python
from django.db.models import F
Product.objects.filter(id__in=product_ids).update(stock=F('stock') - qty)
```

---

### 5. **Используйте aggregate() для расчетов**

❌ **Плохо:**
```python
@property
def total(self):
    return sum(item.subtotal for item in self.items.all())  # Python!
```

✅ **Хорошо:**
```python
def get_total(self):
    from django.db.models import F, Sum
    result = self.items.aggregate(
        total=Sum(F('product__price') * F('quantity'))
    )['total']
    return result or 0
```

---

### 6. **Используйте bulk_create() для множественного создания**

❌ **Плохо:**
```python
for item in items:
    OrderItem.objects.create(**item)  # N запросов!
```

✅ **Хорошо:**
```python
OrderItem.objects.bulk_create([
    OrderItem(**item) for item in items
])  # 1 запрос!
```

---

### 7. **Используйте кэш для часто запрашиваемых данных**

✅ **Хорошо:**
```python
from django.core.cache import cache

cache_key = f'user_cart_{user.id}'
cart_count = cache.get(cache_key)
if cart_count is None:
    cart_count = cart.item_count
    cache.set(cache_key, cart_count, 300)  # 5 мин
```

---

### 8. **Всегда добавляйте db_index для часто используемых полей**

✅ **Хорошо:**
```python
class Product(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    category = models.ForeignKey(..., db_index=True)
    is_featured = models.BooleanField(default=False, db_index=True)
    stock = models.PositiveIntegerField(default=0, db_index=True)
```

---

### 9. **Используйте pagination для больших наборов**

✅ **Хорошо:**
```python
from django.core.paginator import Paginator

paginator = Paginator(products, 20)
page_obj = paginator.get_page(request.GET.get('page'))
```

---

### 10. **Используйте select_for_update() для race conditions**

✅ **Хорошо:**
```python
item, created = CartItem.objects.select_for_update().get_or_create(
    cart=cart, 
    product=product
)
```

---

## 📊 Чек-лист перед commit

- [ ] Нет N+1 запросов (проверить в Django Debug Toolbar)
- [ ] Использованы `select_related()` / `prefetch_related()`
- [ ] Используются `F()` для операций в БД
- [ ] Используется `bulk_create()` для множественного создания
- [ ] Добавлены индексы на новые поля, по которым часто ищут
- [ ] Использован кэш для часто запрашиваемых данных
- [ ] Добавлена pagination если выводится много элементов
- [ ] Коды прошли тесты производительности

---

## 🔧 Инструменты для отладки

### Django Debug Toolbar (development)
```bash
pip install django-debug-toolbar
# Добавить в INSTALLED_APPS и urls.py
```

### django-silk (production monitoring)
```bash
pip install django-silk
# Добавить в INSTALLED_APPS и urls.py
```

### Посмотреть SQL запросы в консоли
```python
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as ctx:
    # ваш код
    print(f"Executed {len(ctx.captured_queries)} queries")
    for query in ctx.captured_queries:
        print(query['sql'])
```

---

## 💾 Environment Variables

Для production используйте:
```bash
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
export SECRET_KEY=your-secret-key-here
```

---

**Спасибо за внимание к производительности! 🚀**
