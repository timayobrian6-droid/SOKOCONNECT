from django.db import migrations
from django.utils.text import slugify

U = "https://images.unsplash.com/photo-{}?auto=format&fit=crop&w=800&q=80"

CATEGORIES = [
    ("produce", "Fresh Produce", "Vegetables, fruits and greens straight from Kenyan farms."),
    ("grains", "Grains & Cereals", "Maize, beans, wheat and other dry staples by the sack."),
    ("meat", "Meat", "Fresh beef, goat meat and lamb from trusted butchers and farmers."),
    ("poultry", "Poultry & Eggs", "Chicken, turkey, ducks and farm-fresh eggs."),
    ("livestock", "Livestock", "Cattle, goats, sheep and pigs from verified livestock farmers."),
    ("dairy", "Dairy Products", "Fresh milk, yoghurt, ghee and other dairy."),
    ("supplies", "Farm Supplies", "Seeds, feeds, fertiliser, tools and equipment."),
]

# (category, subcategory, name, image id, price, old price, rating, reviews, badge, flash, stock, sold, unit, location, description)
PRODUCTS = [
    ("produce", "Tomatoes", "Fresh Ripe Tomatoes — 1 Crate", "1546094096-0df4bcaaa337", 1800, 2200, 4.8, 124, "Top rated", False, 40, 160, "per crate", "Kirinyaga",
     "Firm, ripe tomatoes hand-picked and packed the same day. Ideal for households, restaurants and market vendors. Each crate weighs roughly 60–64kg."),
    ("grains", "Maize", "Dry Maize — 90kg Sack", "1574323347407-f5e1ad6d020b", 3500, 4000, 4.7, 98, "", True, 14, 21, "per 90kg sack", "Trans Nzoia",
     "Well-dried, clean white maize from Kitale. Moisture tested below 13.5% and free from weevils — ready for milling or storage."),
    ("livestock", "Cattle", "Healthy Hereford Breeding Cattle", "1516467508483-a7212febe31a", 85000, 100000, 4.8, 56, "", True, 21, 29, "per head", "Nakuru",
     "Vaccinated, dewormed Hereford breeding stock from a registered ranch. Hardy, fast-growing and well suited to Kenyan conditions. Veterinary records available."),
    ("dairy", "Fresh Milk", "Fresh Cow Milk — 3 Litre Container", "1550583724-b2692b85b150", 300, 360, 4.6, 142, "", True, 3, 47, "per 3L container", "Kiambu",
     "Fresh, chilled whole milk collected every morning from grass-fed dairy cows and delivered in food-grade containers."),
    ("poultry", "Poultry", "Farm-Raised Turkey", "1493962853295-0fd70327578a", 2500, 3000, 4.7, 67, "New", True, 6, 42, "per bird", "Machakos",
     "Free-range turkeys raised on natural feed. Healthy, well-fed birds averaging 6–8kg — perfect for celebrations or breeding."),
    ("grains", "Beans", "Dry Beans — 50kg Bag", "1515543904379-3d757afe72e4", 7000, 7800, 4.6, 83, "", False, 25, 75, "per 50kg bag", "Bungoma",
     "Sorted, clean Rosecoco beans. Rich in protein, quick cooking and free of stones and debris."),
    ("produce", "Leafy Greens", "Fresh Sukuma Wiki Bundle", "1576045057995-568f588f82fb", 150, 200, 4.5, 91, "", False, 120, 380, "per bundle", "Nairobi",
     "Tender sukuma wiki (kale) harvested daily from local growers. Washed and bundled for freshness."),
    ("grains", "Wheat", "Wheat Grain — 90kg Sack", "1500382017468-9049fed747ef", 4200, 4800, 4.6, 52, "", False, 30, 45, "per 90kg sack", "Narok",
     "High-quality hard wheat from Narok farms, cleaned and bagged — great for millers and bakers."),
    ("livestock", "Goats", "Healthy Dairy Goat", "1524024973431-2ad916746881", 18000, 22000, 4.7, 39, "Top rated", False, 12, 18, "per goat", "Nyeri",
     "Toggenburg-cross dairy goat producing 2–3 litres of milk per day. Vaccinated and in great health."),
    ("produce", "Potatoes", "Irish Potatoes — 50kg Bag", "1518977676601-b53f82aba655", 2500, 3000, 4.5, 76, "", False, 60, 140, "per 50kg bag", "Nyandarua",
     "Freshly harvested Shangi potatoes from Nyandarua highlands. Great for chips, mashing and stews."),
    ("poultry", "Eggs", "Farm-Fresh Eggs — Tray of 30", "1518569656558-1f25e69d93d7", 450, 500, 4.6, 110, "", False, 80, 320, "per tray", "Kiambu",
     "Fresh eggs from free-range layers, collected daily and graded by size."),
    ("produce", "Avocados", "Fresh Avocados — 1 Crate", "1523049673857-eb18f1d7b578", 1600, 2000, 4.8, 88, "", False, 35, 95, "per crate", "Murang'a",
     "Creamy Hass avocados from Murang'a. Picked mature and ready to ripen within days."),
    ("meat", "Beef", "Premium Fresh Beef — 1kg", "1625643269470-5d3e7b69fa34", 750, 850, 4.6, 64, "", False, 100, 210, "per kg", "Nairobi",
     "Fresh, tender beef cuts from grass-fed cattle, prepared by a licensed butcher and kept chilled until delivery."),
]


def seed(apps, schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")
    cats = {}
    for pos, (slug, name, desc) in enumerate(CATEGORIES):
        cats[slug], _ = Category.objects.get_or_create(slug=slug, defaults={"name": name, "description": desc, "position": pos})
    for (cat, sub, name, img, price, old, rating, reviews, badge, flash, stock, sold, unit, loc, desc) in PRODUCTS:
        Product.objects.get_or_create(
            slug=slugify(name),
            defaults=dict(
                category=cats[cat], subcategory=sub, name=name, image_url=U.format(img), price=price, old_price=old,
                seed_rating=rating, seed_review_count=reviews, badge=badge, is_flash_deal=flash, stock=stock,
                sold_count=sold, unit=unit, location=loc, description=desc, is_featured=True,
            ),
        )


def unseed(apps, schema_editor):
    apps.get_model("store", "Product").objects.filter(slug__in=[slugify(p[2]) for p in PRODUCTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
