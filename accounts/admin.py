from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['full_name']
    list_display = ['email', 'full_name', 'position', 'department', 'role', 'hourly_rate', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['email', 'full_name']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Shaxsiy ma\'lumot', {'fields': ('full_name', 'phone', 'position', 'department')}),
        ('Ish haqi', {'fields': ('hourly_rate',)}),
        ('Ruxsatlar', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2', 'role', 'hourly_rate'),
        }),
    )
