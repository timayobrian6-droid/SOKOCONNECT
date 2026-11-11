from django import forms

from accounts.forms import StyledFormMixin

from .models import ContactMessage, Order, Product, Review


class ReviewForm(StyledFormMixin, forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(5, 0, -1)], coerce=int
    )

    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {"comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Share your experience with this product"})}


class CheckoutForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ("full_name", "phone", "email", "county", "town", "address", "notes", "payment_method")
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3, "placeholder": "Delivery instructions (optional)"}),
            "payment_method": forms.RadioSelect,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].widget.attrs["class"] = "form-radio"


class ProductForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "subcategory",
            "description",
            "unit",
            "location",
            "price",
            "old_price",
            "stock",
            "image",
            "image_url",
            "is_active",
        )
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}
        labels = {"image_url": "Or image URL", "subcategory": "Product type", "is_active": "Visible on marketplace"}

    def clean(self):
        data = super().clean()
        price, old = data.get("price"), data.get("old_price")
        if old is not None and price is not None and old <= price:
            self.add_error("old_price", "The original price must be higher than the selling price (or leave it blank).")
        return data


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "subject", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}
