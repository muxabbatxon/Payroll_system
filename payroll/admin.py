from django.contrib import admin

from .models import Payroll


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ['employee', 'month', 'year', 'total_hours', 'hourly_rate_snapshot', 'net_salary', 'is_paid']
    list_filter = ['month', 'year', 'is_paid']
    search_fields = ['employee__full_name']
