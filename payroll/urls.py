from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PayrollViewSet, CalculatePayrollView

router = DefaultRouter()
router.register('records', PayrollViewSet, basename='payroll')

urlpatterns = [
    path('calculate/', CalculatePayrollView.as_view(), name='payroll-calculate'),
    path('', include(router.urls)),
]
