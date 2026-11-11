from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, NewsletterSubscriber, Order, Product, WishlistItem

User = get_user_model()
AJAX = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}


class StoreTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.first()
        self.product = Product.objects.active().filter(stock__gte=10).first()
        self.user = User.objects.create_user("jane", "jane@example.com", "S3cure-pass!")


class PageRenderTests(StoreTestCase):
    def test_public_pages_render(self):
        urls = [
            reverse("store:home"),
            reverse("store:product_list"),
            reverse("store:product_list") + "?q=maize&sort=price_asc&in_stock=1",
            reverse("store:category", args=[self.category.slug]),
            self.product.get_absolute_url(),
            reverse("store:cart"),
            reverse("store:contact"),
            reverse("store:page", args=["about"]),
            reverse("store:page", args=["help"]),
            reverse("accounts:login"),
            reverse("accounts:signup"),
            reverse("accounts:password_reset"),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_page_404(self):
        self.assertEqual(self.client.get("/nope-page/").status_code, 404)

    def test_private_pages_require_login(self):
        for name in ["store:checkout", "store:order_list", "store:wishlist", "store:seller_dashboard", "accounts:account"]:
            with self.subTest(name=name):
                res = self.client.get(reverse(name))
                self.assertEqual(res.status_code, 302)
                self.assertIn(reverse("accounts:login"), res["Location"])

    def test_private_pages_render_when_logged_in(self):
        self.client.force_login(self.user)
        for name in ["store:order_list", "store:wishlist", "store:seller_dashboard", "store:product_create",
                     "accounts:account", "accounts:password_change"]:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)


class CartTests(StoreTestCase):
    def test_anonymous_cart_ajax_and_merge_on_login(self):
        res = self.client.post(reverse("store:cart_add", args=[self.product.pk]), {"quantity": 2}, **AJAX)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 2)

        res = self.client.post(reverse("store:cart_update", args=[self.product.pk]), {"quantity": 3}, **AJAX)
        self.assertEqual(res.json()["items"][str(self.product.pk)]["quantity"], 3)

        self.client.post(reverse("accounts:login"), {"username": "jane@example.com", "password": "S3cure-pass!"})
        self.assertEqual(self.user.cart_items.get().quantity, 3)

        res = self.client.post(reverse("store:cart_remove", args=[self.product.pk]), **AJAX)
        self.assertEqual(res.json()["count"], 0)

    def test_quantity_clamped_to_stock(self):
        self.client.post(reverse("store:cart_add", args=[self.product.pk]), {"quantity": 99999}, **AJAX)
        res = self.client.get(reverse("store:cart"))
        self.assertEqual(res.context["items"][0].quantity, self.product.stock)


class CheckoutTests(StoreTestCase):
    checkout_data = {
        "full_name": "Jane Wanjiku", "phone": "0712345678", "email": "jane@example.com",
        "county": "Nairobi", "town": "Westlands", "address": "Hse 4, Rd 2", "payment_method": "mpesa",
    }

    def test_checkout_creates_order_and_cancel_restocks(self):
        self.client.force_login(self.user)
        stock = self.product.stock
        self.client.post(reverse("store:cart_add", args=[self.product.pk]), {"quantity": 2})
        res = self.client.post(reverse("store:checkout"), self.checkout_data)
        order = Order.objects.get(user=self.user)
        self.assertRedirects(res, order.get_absolute_url())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, stock - 2)
        self.assertEqual(order.subtotal, self.product.price * 2)
        expected_fee = Decimal("0") if order.subtotal >= 5000 else Decimal("250")
        self.assertEqual(order.delivery_fee, expected_fee)
        self.assertEqual(self.user.cart_items.count(), 0)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 200)

        self.client.post(reverse("store:order_cancel", args=[order.pk]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.stock, stock)

    def test_other_users_cannot_view_order(self):
        self.client.force_login(self.user)
        self.client.post(reverse("store:cart_add", args=[self.product.pk]), {"quantity": 1})
        self.client.post(reverse("store:checkout"), self.checkout_data)
        order = Order.objects.get()
        other = User.objects.create_user("bob", "bob@example.com", "S3cure-pass!")
        self.client.force_login(other)
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)

    def test_empty_cart_redirects(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(reverse("store:checkout")), reverse("store:cart"))


class WishlistNewsletterReviewTests(StoreTestCase):
    def test_wishlist_requires_login_then_toggles(self):
        url = reverse("store:wishlist_toggle", args=[self.product.pk])
        self.assertEqual(self.client.post(url, **AJAX).status_code, 401)
        self.client.force_login(self.user)
        self.assertTrue(self.client.post(url, **AJAX).json()["saved"])
        self.assertTrue(WishlistItem.objects.filter(user=self.user).exists())
        self.assertFalse(self.client.post(url, **AJAX).json()["saved"])

    def test_newsletter(self):
        url = reverse("store:newsletter")
        self.assertEqual(self.client.post(url, {"email": "bad"}, **AJAX).status_code, 400)
        self.assertTrue(self.client.post(url, {"email": "a@b.co"}, **AJAX).json()["ok"])
        self.assertTrue(self.client.post(url, {"email": "a@b.co"}, **AJAX).json()["ok"])
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)

    def test_review(self):
        self.client.force_login(self.user)
        self.client.post(self.product.get_absolute_url(), {"rating": 4, "comment": "Fresh and tasty"})
        self.assertEqual(self.product.reviews.count(), 1)


class SellerTests(StoreTestCase):
    def test_seller_can_create_edit_and_remove_listing(self):
        self.client.force_login(self.user)
        res = self.client.post(reverse("store:product_create"), {
            "name": "Organic Kale", "category": self.category.pk, "description": "Fresh kale",
            "unit": "per bunch", "location": "Kiambu", "price": "50", "stock": "40", "is_active": "on",
        })
        product = Product.objects.get(name="Organic Kale")
        self.assertEqual(product.seller, self.user)
        self.assertRedirects(res, reverse("store:seller_dashboard"))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_seller)

        other = User.objects.create_user("bob", "bob@example.com", "S3cure-pass!")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("store:product_edit", args=[product.slug])).status_code, 404)

        self.client.force_login(self.user)
        self.client.post(reverse("store:product_delete", args=[product.slug]))
        product.refresh_from_db()
        self.assertFalse(product.is_active)
