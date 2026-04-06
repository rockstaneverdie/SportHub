from django.core.cache import cache
from .models import Cart


def cart_count(request):
    if request.user.is_authenticated:
        cache_key = f'cart_count_{request.user.id}'
        cart_count_value = cache.get(cache_key)
        
        if cart_count_value is None:
            try:
                cart = Cart.objects.get(user=request.user)
                cart_count_value = cart.item_count
                cache.set(cache_key, cart_count_value, 300)
            except Cart.DoesNotExist:
                cart_count_value = 0
        
        return {'cart_count': cart_count_value}
    return {'cart_count': 0}
