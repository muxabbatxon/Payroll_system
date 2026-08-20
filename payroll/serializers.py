from rest_framework import serializers

from .models import Payroll


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    position = serializers.CharField(source='employee.position', read_only=True)

    class Meta:
        model = Payroll
        fields = [
            'id', 'employee', 'employee_name', 'position', 'month', 'year',
            'total_hours', 'hourly_rate_snapshot', 'net_salary',
            'is_paid', 'paid_at', 'calculated_at',
        ]
        read_only_fields = fields


class PayrollCalculateRequestSerializer(serializers.Serializer):
    """POST /api/payroll/calculate/ uchun kirish ma'lumotlarini tekshirish."""
    month = serializers.IntegerField(min_value=1, max_value=12)
    year = serializers.IntegerField(min_value=2000, max_value=2100)
    employee_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, allow_empty=True,
        help_text="Bo'sh qoldirilsa - barcha faol xodimlar uchun hisoblanadi."
    )


class MarkPaidSerializer(serializers.Serializer):
    is_paid = serializers.BooleanField()
