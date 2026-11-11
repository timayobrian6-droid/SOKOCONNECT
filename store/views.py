import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import cart as cart_utils
from .forms import CheckoutForm, ContactForm, ProductForm, ReviewForm
from .models import Category, NewsletterSubscriber, Order, OrderItem, Product, Review, WishlistItem

SORT_OPTIONS = {
    "featured": ("Featured", ["-is_featured", "-created_at"]),
    "newest": ("Newest", ["-created_at"]),
    "price_asc": ("Price: low to high", ["price"]),
    "price_desc": ("Price: high to low", ["-price"]),
    "popular": ("Most popular", ["-sold_count"]),
}


def _wants_json(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get(
        "accept", ""
    )


def _request_data(request):
    if request.content_type == "application/json":
        try:
            return json.loads(request.body or b"{}")
        except ValueError:
            return {}
    return request.POST


def home(request):
    products = Product.objects.active().select_related("category")
    context = {
        "flash_deals": products.filter(is_flash_deal=True, stock__gt=0)[:4],
        "popular_products": products.filter(is_featured=True)[:12],
        "filter_categories": Category.objects.filter(products__is_active=True, products__is_featured=True).distinct(),
    }
    return render(request, "store/home.html", context)


def product_list(request, slug=None):
    products = Product.objects.active().select_related("category")
    category = None
    if slug:
        category = get_object_or_404(Category, slug=slug)
    elif request.GET.get("category") not in (None, "", "all"):
        category = Category.objects.filter(slug=request.GET["category"]).first()
    if category:
        products = products.filter(category=category)

    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(subcategory__icontains=q)
            | Q(description__icontains=q)
            | Q(category__name__icontains=q)
            | Q(location__icontains=q)
        )
    if request.GET.get("deals"):
        products = products.filter(Q(is_flash_deal=True) | Q(old_price__gt=F("price")))
    if request.GET.get("in_stock"):
        products = products.filter(stock__gt=0)

    sort = request.GET.get("sort", "featured")
    if sort not in SORT_OPTIONS:
        sort = "featured"
    products = products.order_by(*SORT_OPTIONS[sort][1])

    page = Paginator(products, 12).get_page(request.GET.get("page"))
    context = {
        "category": category,
        "q": q,
        "page_obj": page,
        "products": page.object_list,
        "sort": sort,
        "sort_options": [(k, v[0]) for k, v in SORT_OPTIONS.items()],
        "total": page.paginator.count,
    }
    return render(request, "store/product_list.html", context)


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "seller"), slug=slug)
    if not product.is_active and product.seller != request.user and not request.user.is_staff:
        return render(request, "404.html", status=404)

    user_review = None
    if request.user.is_authenticated:
        user_review = product.reviews.filter(user=request.user).first()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('accounts:login')}?next={product.get_absolute_url()}")
        form = ReviewForm(request.POST, instance=user_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thanks! Your review has been saved.")
            return redirect(f"{product.get_absolute_url()}#tab-reviews")
    else:
        form = ReviewForm(instance=user_review)

    reviews = product.reviews.select_related("user")
    summary = product.rating_summary()
    breakdown = []
    total_real = reviews.count()
    for star in range(5, 0, -1):
        n = reviews.filter(rating=star).count()
        breakdown.append({"star": star, "pct": int(n * 100 / total_real) if total_real else 0})

    related = (
        Product.objects.active().filter(category=product.category).exclude(pk=product.pk).select_related("category")[:4]
    )
    return render(
        request,
        "store/product_detail.html",
        {
            "product": product,
            "reviews": reviews,
            "review_form": form,
            "user_review": user_review,
            "summary": summary,
            "breakdown": breakdown,
            "related": related,
        },
    )


# ---------- cart ----------


def _cart_payload(request, message=None):
    items = list(cart_utils.cart_items(request))
    totals = cart_utils.cart_totals(items)
    return {
        "ok": True,
        "message": message,
        "count": sum(i.quantity for i in items),
        "subtotal": float(totals["subtotal"]),
        "delivery": float(totals["delivery"]),
        "total": float(totals["total"]),
        "items": {str(i.product_id): {"quantity": i.quantity, "line_total": float(i.line_total)} for i in items},
    }


def cart_detail(request):
    items = list(cart_utils.cart_items(request))
    return render(request, "store/cart.html", {"items": items, **cart_utils.cart_totals(items)})


@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    data = _request_data(request)
    try:
        qty = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    if not product.in_stock:
        msg = f"Sorry, {product.name} is out of stock."
        if _wants_json(request):
            return JsonResponse({"ok": False, "message": msg}, status=400)
        messages.error(request, msg)
        return redirect(product.get_absolute_url())
    cart_utils.add_to_cart(request, product, qty)
    msg = f"{product.name} added to cart"
    if _wants_json(request):
        return JsonResponse(_cart_payload(request, msg))
    messages.success(request, msg)
    if data.get("buy_now"):
        return redirect("store:checkout")
    return redirect(request.META.get("HTTP_REFERER") or "store:cart")


@require_POST
def cart_update(request, product_id):
    data = _request_data(request)
    try:
        qty = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        qty = 1
    cart_utils.set_quantity(request, product_id, qty)
    if _wants_json(request):
        return JsonResponse(_cart_payload(request, "Cart updated"))
    return redirect("store:cart")


@require_POST
def cart_remove(request, product_id):
    cart_utils.remove_from_cart(request, product_id)
    if _wants_json(request):
        return JsonResponse(_cart_payload(request, "Item removed from cart"))
    messages.info(request, "Item removed from cart.")
    return redirect("store:cart")


# ---------- checkout & orders ----------


@login_required
def checkout(request):
    items = list(cart_utils.cart_items(request))
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect("store:cart")
    totals = cart_utils.cart_totals(items)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                locked = {p.pk: p for p in Product.objects.select_for_update().filter(pk__in=[i.product_id for i in items])}
                problems = [i.product.name for i in items if locked[i.product_id].stock < i.quantity]
                if problems:
                    messages.error(request, "Not enough stock for: " + ", ".join(problems) + ". Please adjust your cart.")
                    return redirect("store:cart")
                order = form.save(commit=False)
                order.user = request.user
                order.subtotal = totals["subtotal"]
                order.delivery_fee = totals["delivery"]
                order.total = totals["total"]
                order.save()
                for i in items:
                    OrderItem.objects.create(
                        order=order,
                        product=i.product,
                        product_name=i.product.name,
                        unit_price=i.product.price,
                        quantity=i.quantity,
                    )
                    Product.objects.filter(pk=i.product_id).update(
                        stock=F("stock") - i.quantity, sold_count=F("sold_count") + i.quantity
                    )
                cart_utils.clear_cart(request)
            messages.success(request, f"Order {order.number} placed successfully!")
            return redirect(order.get_absolute_url())
    else:
        profile = request.user.profile
        form = CheckoutForm(
            initial={
                "full_name": request.user.get_full_name(),
                "email": request.user.email,
                "phone": profile.phone,
                "county": profile.county,
                "town": profile.town,
                "address": profile.address,
            }
        )
    return render(request, "store/checkout.html", {"form": form, "items": items, **totals})


@login_required
def order_list(request):
    orders = request.user.orders.prefetch_related("items")
    return render(request, "store/order_list.html", {"orders": orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=pk, user=request.user)
    return render(request, "store/order_detail.html", {"order": order})


@login_required
@require_POST
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status != Order.Status.PENDING:
        messages.error(request, "Only pending orders can be cancelled.")
        return redirect(order.get_absolute_url())
    with transaction.atomic():
        for item in order.items.all():
            if item.product_id:
                Product.objects.filter(pk=item.product_id).update(
                    stock=F("stock") + item.quantity, sold_count=F("sold_count") - item.quantity
                )
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
    messages.info(request, f"Order {order.number} was cancelled.")
    return redirect(order.get_absolute_url())


# ---------- wishlist ----------


@require_POST
def wishlist_toggle(request, product_id):
    if not request.user.is_authenticated:
        login_url = f"{reverse('accounts:login')}?next={request.META.get('HTTP_REFERER', '/')}"
        if _wants_json(request):
            return JsonResponse({"ok": False, "login_url": login_url, "message": "Log in to save items"}, status=401)
        return redirect(login_url)
    product = get_object_or_404(Product, pk=product_id)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
    count = WishlistItem.objects.filter(user=request.user).count()
    msg = "Saved to wishlist" if created else "Removed from wishlist"
    if _wants_json(request):
        return JsonResponse({"ok": True, "saved": created, "count": count, "message": msg})
    messages.success(request, msg)
    return redirect(request.META.get("HTTP_REFERER") or "store:wishlist")


@login_required
def wishlist(request):
    items = request.user.wishlist.select_related("product", "product__category")
    return render(request, "store/wishlist.html", {"items": items})


# ---------- newsletter & contact ----------


@require_POST
def newsletter_subscribe(request):
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

    email = (_request_data(request).get("email") or "").strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        if _wants_json(request):
            return JsonResponse({"ok": False, "message": "Please enter a valid email address."}, status=400)
        messages.error(request, "Please enter a valid email address.")
        return redirect(request.META.get("HTTP_REFERER") or "store:home")
    _, created = NewsletterSubscriber.objects.get_or_create(email=email)
    msg = "You're in! Check your inbox for a 15% welcome code." if created else "You're already subscribed."
    if _wants_json(request):
        return JsonResponse({"ok": True, "message": msg})
    messages.success(request, msg)
    return redirect(request.META.get("HTTP_REFERER") or "store:home")


def contact(request):
    initial = {}
    if request.user.is_authenticated:
        initial = {"name": request.user.get_full_name(), "email": request.user.email}
    form = ContactForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks for reaching out — our team will get back to you shortly.")
        return redirect("store:contact")
    return render(request, "store/contact.html", {"form": form})


def page(request, name):
    templates = {"about": "store/pages/about.html", "help": "store/pages/help.html"}
    if name not in templates:
        return render(request, "404.html", status=404)
    return render(request, templates[name])


# ---------- seller dashboard ----------


def _require_seller(request):
    profile = request.user.profile
    if not profile.is_seller:
        profile.is_seller = True
        profile.save(update_fields=["is_seller"])
        messages.info(request, "Your seller account is now active.")


@login_required
def seller_dashboard(request):
    _require_seller(request)
    listings = request.user.listings.select_related("category").order_by("-created_at")
    sales = (
        OrderItem.objects.filter(product__seller=request.user)
        .exclude(order__status=Order.Status.CANCELLED)
        .select_related("order")
        .order_by("-order__created_at")[:20]
    )
    return render(request, "store/seller/dashboard.html", {"listings": listings, "sales": sales})


@login_required
def product_create(request):
    _require_seller(request)
    form = ProductForm(request.POST or None, request.FILES or None, initial={"location": request.user.profile.town})
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user
        product.is_featured = False
        product.save()
        messages.success(request, f"{product.name} is now listed on SokoConnect.")
        return redirect("store:seller_dashboard")
    return render(request, "store/seller/product_form.html", {"form": form, "title": "List a new product"})


@login_required
def product_edit(request, slug):
    product = get_object_or_404(Product, slug=slug, seller=request.user)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Listing updated.")
        return redirect("store:seller_dashboard")
    return render(request, "store/seller/product_form.html", {"form": form, "title": f"Edit {product.name}", "product": product})


@login_required
@require_POST
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug, seller=request.user)
    product.is_active = False
    product.save(update_fields=["is_active"])
    messages.info(request, f"{product.name} was removed from the marketplace.")
    return redirect("store:seller_dashboard")
