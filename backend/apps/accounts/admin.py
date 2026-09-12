from typing import Any, cast

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class AdviserUserAdmin(UserAdmin):  # type: ignore[type-arg]
    model = User
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active")
    fieldsets = ((None, {"fields": ("email", "password")}),) + cast(Any, UserAdmin.fieldsets)[2:]
    add_fieldsets = ((None, {"fields": ("email", "password1", "password2")}),)
