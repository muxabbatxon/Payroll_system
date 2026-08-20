from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from attendance.models import Attendance
from .models import User
from .permissions import IsHR
from .serializers import (
    EmailTokenObtainPairSerializer,
    UserListSerializer,
    UserCreateUpdateSerializer,
    MeSerializer,
)


class EmailTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/  -> {email, password} orqali JWT token olish."""
    serializer_class = EmailTokenObtainPairSerializer


class MeView(generics.RetrieveAPIView):
    """GET /api/accounts/me/ - joriy tizimga kirgan foydalanuvchi profili."""
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Xodimlar bo'yicha CRUD.
    - Ro'yxat/detail: HR va Xodim ko'ra oladi (xodim faqat o'zinikini - get_queryset orqali cheklanadi).
    - Yaratish/yangilash/o'chirish: faqat HR.
    """
    queryset = User.objects.all()
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['full_name', 'email', 'position']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserListSerializer
        return UserCreateUpdateSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [IsHR()]

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.all().order_by('full_name')
        if user.role != User.Role.HR:

            return qs.filter(id=user.id)
        return qs


class DashboardView(APIView):
    """
    GET /api/accounts/dashboard/
    HR Admin uchun bosh sahifa statistikasi:
    - jami xodimlar soni
    - bugun kelmagan xodimlar soni
    - shu oy uchun taxminiy/hisoblangan byudjet
    """
    permission_classes = [IsHR]

    def get(self, request):
        today = timezone.localdate()

        total_employees = User.objects.filter(role=User.Role.EMPLOYEE, is_active=True).count()

        absent_today = Attendance.objects.filter(
            date=today, status=Attendance.Status.ABSENT
        ).count()


        month_start = today.replace(day=1)
        monthly_qs = Attendance.objects.filter(
            date__gte=month_start, date__lte=today
        ).select_related('employee')

        estimated_budget = sum(
            (a.hours_worked * a.employee.hourly_rate for a in monthly_qs),
        ) or 0

        return Response({
            'total_employees': total_employees,
            'absent_today': absent_today,
            'estimated_monthly_budget': estimated_budget,
            'month': today.month,
            'year': today.year,
        })
