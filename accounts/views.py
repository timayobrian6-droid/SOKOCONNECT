from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, ProfileUpdateForm, SignUpForm, UserUpdateForm


def signup(request):
    if request.user.is_authenticated:
        return redirect("store:home")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="accounts.backends.EmailOrUsernameBackend")
            messages.success(request, f"Welcome to SokoConnect, {user.first_name}!")
            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url if next_url and next_url.startswith("/") else "store:home")
    else:
        form = SignUpForm()
    return render(request, "accounts/signup.html", {"form": form, "next": request.GET.get("next", "")})


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        if not form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(0)
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {self.request.user.first_name or self.request.user.username}!")
        return response


class LogoutView(auth_views.LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been logged out.")
        return response


@login_required
def account(request):
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your account details were updated.")
            return redirect("accounts:account")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    recent_orders = request.user.orders.all()[:5]
    return render(
        request,
        "accounts/account.html",
        {"user_form": user_form, "profile_form": profile_form, "recent_orders": recent_orders},
    )


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:account")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "form-input")
        return form

    def form_valid(self, form):
        messages.success(self.request, "Your password was changed.")
        return super().form_valid(form)


class StyledPasswordResetMixin:
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.setdefault("class", "form-input")
        return form


class PasswordResetView(StyledPasswordResetMixin, auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetConfirmView(StyledPasswordResetMixin, auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
