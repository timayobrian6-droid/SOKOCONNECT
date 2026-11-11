from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("category/<slug:slug>/", views.product_list, name="category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("orders/", views.order_list, name="order_list"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/cancel/", views.order_cancel, name="order_cancel"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:product_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("newsletter/", views.newsletter_subscribe, name="newsletter"),
    path("contact/", views.contact, name="contact"),
    path("sell/", views.seller_dashboard, name="seller_dashboard"),
    path("sell/new/", views.product_create, name="product_create"),
    path("sell/<slug:slug>/edit/", views.product_edit, name="product_edit"),
    path("sell/<slug:slug>/delete/", views.product_delete, name="product_delete"),
    path("<str:name>/", views.page, name="page"),
]
