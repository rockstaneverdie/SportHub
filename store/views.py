from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.db.models import Q, F, Sum, DecimalField
from django.core.paginator import Paginator
from django import forms
from .models import Category, Product, Cart, CartItem, Order, OrderItem


def home(request):
    categories = Category.objects.all()
    featured = Product.objects.filter(is_featured=True, stock__gt=0)[:8]
    new_arrivals = Product.objects.filter(stock__gt=0)[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'featured': featured,
        'new_arrivals': new_arrivals,
    })


def catalog(request):
    categories = Category.objects.all()
    products = Product.objects.filter(stock__gt=0).select_related('category')
    category_slug = request.GET.get('category')
    search = request.GET.get('q', '')
    sort = request.GET.get('sort', '-created_at')

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    if search:
        products = products.filter(Q(name__icontains=search) | Q(description__icontains=search)).distinct()

    sort_options = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created_at',
        'name': 'name',
    }
    products = products.order_by(sort_options.get(sort, '-created_at'))
    
    # Пагинация
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'store/catalog.html', {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'categories': categories,
        'active_category': active_category,
        'search': search,
        'sort': sort,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug)
    related = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related': related,
    })


@login_required
def cart_view(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.select_related('product')
    return render(request, 'store/cart.html', {'cart': cart})


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.select_for_update().get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save(update_fields=['quantity'])
    messages.success(request, f'«{product.name}» добавлен в корзину!')
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    messages.info(request, 'Товар удалён из корзины.')
    return redirect('cart')


@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return redirect('cart')


@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.error(request, 'Корзина пуста.')
        return redirect('cart')

    if request.method == 'POST':
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        if not address or not phone:
            messages.error(request, 'Заполните все поля.')
            return render(request, 'store/checkout.html', {'cart': cart})

        order = Order.objects.create(
            user=request.user,
            total=cart.total,
            address=address,
            phone=phone,
        )
        
        # Оптимизированный способ сохранения items и обновления stock
        items_to_create = []
        product_ids_to_update = []
        
        for item in cart.items.all():
            items_to_create.append(OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price,
            ))
            product_ids_to_update.append((item.product.id, item.quantity))
        
        OrderItem.objects.bulk_create(items_to_create)
        
        # Bulk update stock с использованием F()
        for prod_id, qty in product_ids_to_update:
            Product.objects.filter(id=prod_id).update(stock=F('stock') - qty)
        
        cart.items.all().delete()
        messages.success(request, f'Заказ #{order.id} успешно оформлен!')
        return redirect('order_detail', order_id=order.id)

    return render(request, 'store/checkout.html', {'cart': cart})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items', 'items__product').order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.GET.get('next', '/'))
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Аккаунт создан! Добро пожаловать!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'store/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


class UserProfileForm(forms.Form):
    username = forms.CharField(max_length=150, label='Имя пользователя')
    email = forms.EmailField(label='Email', required=False)


@login_required
def account_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            form = UserProfileForm(request.POST)
            if form.is_valid():
                user = request.user
                new_username = form.cleaned_data['username']
                new_email = form.cleaned_data['email']
                
                # Проверка уникальности имени пользователя
                if new_username != user.username and user.__class__.objects.filter(username=new_username).exclude(id=user.id).exists():
                    messages.error(request, 'Это имя пользователя уже занято.')
                else:
                    user.username = new_username
                    user.email = new_email
                    user.save()
                    messages.success(request, 'Профиль успешно обновлён!')
                    return redirect('account')
        
        elif action == 'change_password':
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Пароль успешно изменён!')
                return redirect('account')
            else:
                messages.error(request, 'Ошибка при смене пароля. Проверьте введённые данные.')
        
        elif action == 'delete_account':
            password = request.POST.get('password', '')
            if authenticate(username=request.user.username, password=password):
                user = request.user
                user.delete()
                messages.success(request, 'Аккаунт удалён.')
                return redirect('home')
            else:
                messages.error(request, 'Неверный пароль.')
    
    profile_form = UserProfileForm(initial={
        'username': request.user.username,
        'email': request.user.email,
    })
    password_form = PasswordChangeForm(request.user)
    
    return render(request, 'store/account.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })
