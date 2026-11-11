from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile

User = get_user_model()


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                widget.attrs.setdefault("class", "form-input")


class SignUpForm(StyledFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False, help_text="e.g. 0712 345 678")
    is_seller = forms.BooleanField(required=False, label="I also want to sell my farm products")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data.get("phone", "")
            profile.is_seller = self.cleaned_data.get("is_seller", False)
            profile.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(label="Username or email", max_length=254)
    remember_me = forms.BooleanField(required=False, initial=True, label="Keep me signed in")


class UserUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another account already uses this email.")
        return email


class ProfileUpdateForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "county", "town", "address", "is_seller")
        labels = {"is_seller": "I want to sell on SokoConnect"}
