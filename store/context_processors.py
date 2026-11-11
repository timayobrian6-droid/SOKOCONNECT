from .cart import cart_count
from .models import Category, WishlistItem


def store(request):
    wish_ids = set()
    if request.user.is_authenticated:
        wish_ids = set(WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True))
    return {
        "nav_categories": Category.objects.all(),
        "cart_count": cart_count(request),
        "wishlist_ids": wish_ids,
        "wishlist_count": len(wish_ids),
    }
