from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Profile

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = [ProfileInline]
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "date_joined")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "county", "town", "is_seller")
    list_filter = ("is_seller", "county")
    search_fields = ("user__username", "user__email", "phone")
