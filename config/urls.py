from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import EmailTokenObtainPairView
from django.contrib import admin
from django.urls import path




urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Ilovalar
    path('api/accounts/', include('accounts.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/payroll/', include('payroll.urls')),
]
