# SokoConnect

SokoConnect is a Django marketplace for Kenyan farm products — produce, grains, livestock, dairy and farm supplies.

## Features

- **Accounts** – sign up, log in with username *or* email, log out, profile editing, password change and password reset (emails print to the console in development).
- **Marketplace** – home page with flash deals and popular products, category pages, search, sorting, in-stock filter, pagination and product detail pages with reviews.
- **Cart** – works for guests and logged-in users; guest carts are merged into the user's cart on login. Free delivery over KSh 5,000, otherwise KSh 250.
- **Checkout & orders** – M-Pesa / cash / card on delivery, stock is reserved at checkout, order history and cancellation (stock is restored).
- **Wishlist & newsletter** – AJAX heart toggle and newsletter signup.
- **Seller dashboard** – any user can list, edit and hide products and see their sales.
- **Admin** – manage everything at `/admin/`.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate          # creates db.sqlite3 and seeds categories/products
python manage.py createsuperuser  # optional, for /admin/
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Tests

```bash
python manage.py test
```

## Project layout

```
sokoconnect/   Django settings and root URLs
accounts/      signup, login (username/email backend), profile
store/         products, cart, wishlist, orders, reviews, seller tools
templates/     Django templates
static/        CSS, JS (static/js/main.js) and images
```

## Production notes

Set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0` and `DJANGO_ALLOWED_HOSTS`, configure a real email backend, and run `python manage.py collectstatic`.
