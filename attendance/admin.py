from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'hours_worked', 'status']
    list_filter = ['status', 'date']
    search_fields = ['employee__full_name']
    date_hierarchy = 'date'
