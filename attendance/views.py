import calendar

from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsHR, IsHRorReadOnlySelf
from .models import Attendance
from .serializers import AttendanceSerializer, AttendanceCellUpsertSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    Davomat (Tabel) uchun asosiy CRUD API.

    - HR Admin: barcha xodimlarning davomatini ko'radi, yozadi, o'zgartiradi, o'chiradi.
    - Xodim: faqat o'zining davomatini (read-only) ko'ra oladi.

    Qo'shimcha endpointlar:
    - POST /api/attendance/records/save_cell/  -> Tabel jadvalidagi bitta katakni Autosave qilish (Upsert)
    - GET  /api/attendance/records/monthly_grid/?month=4&year=2026 -> butun oy uchun Excel-simon grid
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsHRorReadOnlySelf]

    def get_queryset(self):
        qs = Attendance.objects.select_related('employee').all()
        user = self.request.user

        if user.role != User.Role.HR:
            qs = qs.filter(employee=user)

        employee_id = self.request.query_params.get('employee')
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')

        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)

        return qs.order_by('-date')

    @action(detail=False, methods=['post'], permission_classes=[IsHR])
    def save_cell(self, request):
        """
        Tabel gridida bitta katak (xodim + sana) uchun ma'lumotni saqlaydi.
        Katakdan chiqilishi bilan (onBlur) frontend shu endpointga so'rov yuboradi -> Autosave.
        Upsert logikasi: mavjud bo'lsa UPDATE, bo'lmasa CREATE.
        """
        serializer = AttendanceCellUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        created = getattr(serializer, '_created', False)

        output = AttendanceSerializer(instance)
        return Response(
            output.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'])
    def monthly_grid(self, request):
        """
        Excel-ga o'xshash Tabel grid uchun ma'lumot.
        Har bir xodim va oyning har bir kuni bo'yicha (hatto yozuv bo'lmasa ham) qator qaytaradi,
        frontend buni to'g'ridan-to'g'ri jadval sifatida chizishi mumkin.
        """
        today = timezone.localdate()
        month = int(request.query_params.get('month', today.month))
        year = int(request.query_params.get('year', today.year))
        days_in_month = calendar.monthrange(year, month)[1]

        user = request.user
        if user.role == User.Role.HR:
            employees = User.objects.filter(role=User.Role.EMPLOYEE, is_active=True).order_by('full_name')
        else:
            employees = User.objects.filter(id=user.id)

        records = Attendance.objects.filter(
            date__year=year, date__month=month, employee__in=employees
        )
        record_map = {(r.employee_id, r.date.day): r for r in records}

        result = []
        for emp in employees:
            days = []
            for day in range(1, days_in_month + 1):
                rec = record_map.get((emp.id, day))
                days.append({
                    'day': day,
                    'hours_worked': str(rec.hours_worked) if rec else None,
                    'status': rec.status if rec else None,
                    'attendance_id': rec.id if rec else None,
                })
            result.append({
                'employee_id': emp.id,
                'employee_name': emp.full_name,
                'position': emp.position,
                'days': days,
            })

        return Response({
            'month': month,
            'year': year,
            'days_in_month': days_in_month,
            'employees': result,
        })
