from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django.utils.text import slugify


def unique_slug(instance, value, max_length=60):
    base = slugify(value)[:max_length] or "item"
    slug, n = base, 2
    Model = type(instance)
    while Model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        suffix = f"-{n}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}"
        n += 1
    return slug


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("store:category", args=[self.slug])


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="listings"
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    subcategory = models.CharField(max_length=60, blank=True, help_text="Short label shown on cards, e.g. 'Tomatoes'.")
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=40, blank=True, help_text="e.g. 'per crate', 'per 90kg sack'.")
    location = models.CharField(max_length=80, blank=True, help_text="County / town where the product is.")
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("1"))])
    old_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, help_text="Original price, shown struck through."
    )
    stock = models.PositiveIntegerField(default=10)
    sold_count = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    badge = models.CharField(max_length=30, blank=True, help_text="Optional badge e.g. 'Top rated', 'New'.")
    is_flash_deal = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    seed_rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    seed_review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-is_featured", "-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 170)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("store:product_detail", args=[self.slug])

    @property
    def image_src(self):
        if self.image:
            return self.image.url
        return self.image_url or f"{settings.STATIC_URL}img/p-vacuum.jpg"

    @property
    def discount_percent(self):
        if self.old_price and self.old_price > self.price:
            return int(round((1 - self.price / self.old_price) * 100))
        return 0

    @property
    def savings(self):
        if self.old_price and self.old_price > self.price:
            return self.old_price - self.price
        return Decimal("0")

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def stock_fill(self):
        total = self.stock + self.sold_count
        return int(self.stock * 100 / total) if total else 0

    def rating_summary(self):
        agg = self.reviews.aggregate(avg=Avg("rating"), count=Count("id"))
        real_count = agg["count"] or 0
        total = real_count + self.seed_review_count
        if not total:
            return {"rating": 0, "count": 0}
        real_sum = (agg["avg"] or 0) * real_count
        avg = (real_sum + float(self.seed_rating) * self.seed_review_count) / total
        return {"rating": round(avg, 1), "count": total}

    @property
    def rating(self):
        return self.rating_summary()["rating"]

    @property
    def review_count(self):
        return self.rating_summary()["count"]


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["product", "user"], name="one_review_per_user_product")]

    def __str__(self):
        return f"{self.rating}★ {self.product} by {self.user}"

    @property
    def verified_purchase(self):
        return OrderItem.objects.filter(order__user=self.user, product=self.product).exists()


class CartItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items"
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["added_at"]

    def __str__(self):
        return f"{self.quantity} × {self.product}"

    @property
    def line_total(self):
        return self.product.price * self.quantity


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]
        constraints = [models.UniqueConstraint(fields=["user", "product"], name="unique_wishlist_item")]

    def __str__(self):
        return f"{self.user} ♥ {self.product}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        SHIPPED = "shipped", "Out for delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"
        CASH = "cash", "Cash on delivery"
        CARD = "card", "Card on delivery"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    county = models.CharField(max_length=60)
    town = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.MPESA)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.number}"

    @property
    def number(self):
        return f"SC{self.pk:06d}" if self.pk else "SC------"

    def get_absolute_url(self):
        return reverse("store:order_detail", args=[self.pk])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=160)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    subject = models.CharField(max_length=160)
    message = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} — {self.email}"
