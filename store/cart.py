"""Cart helpers: DB-backed cart for both signed-in users and anonymous sessions."""

import uuid
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum

from .models import CartItem


CART_SESSION_KEY = "cart_token"


def _session_key(request, create=False):
    # A token stored inside the session survives the key rotation that happens on login.
    token = request.session.get(CART_SESSION_KEY)
    if not token and create:
        token = uuid.uuid4().hex
        request.session[CART_SESSION_KEY] = token
    return token


def cart_items(request):
    if request.user.is_authenticated:
        qs = CartItem.objects.filter(user=request.user)
    else:
        key = _session_key(request)
        if not key:
            return CartItem.objects.none()
        qs = CartItem.objects.filter(user__isnull=True, session_key=key)
    return qs.select_related("product", "product__category")


def cart_count(request):
    return cart_items(request).aggregate(n=Sum("quantity"))["n"] or 0


def add_to_cart(request, product, quantity=1):
    quantity = max(1, int(quantity))
    if request.user.is_authenticated:
        item, created = CartItem.objects.get_or_create(user=request.user, product=product, defaults={"quantity": 0})
    else:
        key = _session_key(request, create=True)
        item, created = CartItem.objects.get_or_create(
            user=None, session_key=key, product=product, defaults={"quantity": 0}
        )
    item.quantity = min(item.quantity + quantity, max(product.stock, 1))
    item.save()
    return item


def set_quantity(request, product_id, quantity):
    item = cart_items(request).filter(product_id=product_id).first()
    if not item:
        return None
    quantity = int(quantity)
    if quantity <= 0:
        item.delete()
        return None
    item.quantity = min(quantity, max(item.product.stock, 1))
    item.save()
    return item


def remove_from_cart(request, product_id):
    cart_items(request).filter(product_id=product_id).delete()


def clear_cart(request):
    cart_items(request).delete()


def cart_totals(items):
    subtotal = sum((i.line_total for i in items), Decimal("0"))
    if not items or subtotal >= settings.FREE_DELIVERY_THRESHOLD:
        delivery = Decimal("0")
    else:
        delivery = Decimal(settings.DELIVERY_FEE)
    return {"subtotal": subtotal, "delivery": delivery, "total": subtotal + delivery}


def merge_anonymous_cart(request, user):
    """Called on login: move items from the anonymous session cart into the user's cart."""
    key = request.session.get(CART_SESSION_KEY)
    if not key:
        return
    for item in CartItem.objects.filter(user__isnull=True, session_key=key).select_related("product"):
        existing = CartItem.objects.filter(user=user, product=item.product).first()
        if existing:
            existing.quantity = min(existing.quantity + item.quantity, max(item.product.stock, 1))
            existing.save()
            item.delete()
        else:
            item.user = user
            item.session_key = ""
            item.save()

