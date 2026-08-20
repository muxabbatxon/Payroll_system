from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsHR, IsHRorReadOnlySelf
from .models import Payroll
from .serializers import PayrollSerializer, PayrollCalculateRequestSerializer, MarkPaidSerializer
from .services import calculate_payroll_bulk


class PayrollViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Hisoblangan oyliklarni ko'rish uchun (read-only - hisoblash alohida CalculatePayrollView orqali).

    - HR: barcha xodimlarning oyliklarini ko'radi, filtrlaydi (?month=&year=&employee=).
    - Xodim: faqat o'zining oylik varaqalarini ('Mening Maoshim') ko'ra oladi.
    """
    serializer_class = PayrollSerializer
    permission_classes = [IsHRorReadOnlySelf]

    def get_queryset(self):
        qs = Payroll.objects.select_related('employee').all()
        user = self.request.user
        if user.role != User.Role.HR:
            qs = qs.filter(employee=user)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        employee_id = self.request.query_params.get('employee')

        if month:
            qs = qs.filter(month=month)
        if year:
            qs = qs.filter(year=year)
        if employee_id:
            qs = qs.filter(employee_id=employee_id)

        return qs.order_by('-year', '-month', 'employee__full_name')

    @action(detail=True, methods=['patch'], permission_classes=[IsHR])
    def mark_paid(self, request, pk=None):
        """PATCH /api/payroll/records/{id}/mark_paid/ -> {"is_paid": true} - oylik to'landi deb belgilash."""
        payroll = self.get_object()
        serializer = MarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payroll.is_paid = serializer.validated_data['is_paid']
        payroll.paid_at = timezone.now() if payroll.is_paid else None
        payroll.save(update_fields=['is_paid', 'paid_at'])

        return Response(PayrollSerializer(payroll).data)


class CalculatePayrollView(APIView):
    """
    POST /api/payroll/calculate/
    Body: { "month": 4, "year": 2026, "employee_ids": [1,2,3] }  (employee_ids ixtiyoriy)

    "Oylikni hisoblash" tugmasi bosilganda chaqiriladigan asosiy API.
    Barcha (yoki tanlangan) faol xodimlar uchun shu oydagi Attendance yozuvlarini
    yig'ib, Net Salary ni hisoblab, Payroll jadvaliga saqlaydi.

    Faqat HR Admin foydalana oladi.
    """
    permission_classes = [IsHR]

    def post(self, request):
        req = PayrollCalculateRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        month = req.validated_data['month']
        year = req.validated_data['year']
        employee_ids = req.validated_data.get('employee_ids') or None

        payrolls = calculate_payroll_bulk(month=month, year=year, employee_ids=employee_ids)

        return Response(
            {
                'message': f"{month}-{year} oyi uchun {len(payrolls)} ta xodimning oyligi hisoblandi.",
                'results': PayrollSerializer(payrolls, many=True).data,
            },
            status=status.HTTP_200_OK,
        )
