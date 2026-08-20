from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from accounts.models import User
from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'date',
            'hours_worked', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance, 'status', Attendance.Status.PRESENT))
        hours = attrs.get('hours_worked', getattr(self.instance, 'hours_worked', Decimal('0.00')))

        if status == Attendance.Status.ABSENT:
            attrs['hours_worked'] = Decimal('0.00')
        else:
            if hours is None or hours < 0:
                raise serializers.ValidationError({'hours_worked': "Ishlangan soat manfiy bo'la olmaydi."})
            if hours > 24:
                raise serializers.ValidationError({'hours_worked': "Bir kunda 24 soatdan ortiq bo'lishi mumkin emas."})
        return attrs


class AttendanceCellUpsertSerializer(serializers.Serializer):
    """
    Tabel (Excel-ga o'xshash grid) jadvalidagi bitta katakni saqlash uchun.
    HR bitta katakka qiymat kiritganda, frontend shu formatda so'rov yuboradi:
    { "employee": 5, "date": "2026-04-15", "hours_worked": 8, "status": "PRESENT" }

    Backend: agar shu (employee, date) uchun yozuv bo'lsa -> UPDATE,
             bo'lmasa -> CREATE (Upsert).
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    date = serializers.DateField()
    hours_worked = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, default=Decimal('0.00')
    )
    status = serializers.ChoiceField(choices=Attendance.Status.choices, default=Attendance.Status.PRESENT)

    def validate(self, attrs):
        if attrs.get('status') == Attendance.Status.ABSENT:
            attrs['hours_worked'] = Decimal('0.00')
        elif attrs.get('hours_worked', Decimal('0.00')) < 0:
            raise serializers.ValidationError({'hours_worked': "Manfiy bo'la olmaydi."})
        elif attrs.get('hours_worked', Decimal('0.00')) > 24:
            raise serializers.ValidationError({'hours_worked': "24 soatdan ortiq bo'la olmaydi."})
        return attrs

    def save(self, **kwargs):
        validated = self.validated_data
        instance, created = Attendance.objects.update_or_create(
            employee=validated['employee'],
            date=validated['date'],
            defaults={
                'hours_worked': validated.get('hours_worked', Decimal('0.00')),
                'status': validated.get('status', Attendance.Status.PRESENT),
            },
        )
        self._created = created
        return instance
