from django.contrib import admin

from .models import CartItem, Category, ContactMessage, NewsletterSubscriber, Order, OrderItem, Product, Review, WishlistItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "position")
    list_editable = ("position",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "old_price", "stock", "sold_count", "seller", "is_flash_deal", "is_featured", "is_active")
    list_filter = ("category", "is_flash_deal", "is_featured", "is_active")
    list_editable = ("price", "stock", "is_flash_deal", "is_featured", "is_active")
    search_fields = ("name", "subcategory", "description", "location")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("seller",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "full_name", "phone", "total", "payment_method", "status", "created_at")
    list_filter = ("status", "payment_method", "created_at")
    list_editable = ("status",)
    search_fields = ("id", "full_name", "phone", "email", "user__username")
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("product__name", "user__username", "comment")


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "name", "email", "created_at", "is_resolved")
    list_filter = ("is_resolved",)
    list_editable = ("is_resolved",)


admin.site.register(CartItem)
admin.site.register(WishlistItem)
admin.site.register(NewsletterSubscriber)
