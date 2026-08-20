from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import EmployeeViewSet, MeView, DashboardView

router = DefaultRouter()
router.register('employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('me/', MeView.as_view(), name='me'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('', include(router.urls)),
]
