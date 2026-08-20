from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import EmailTokenObtainPairView
from django.contrib import admin
from django.urls import path
from django.contrib import admin
from django.urls import path
from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_admin_quick(request):
    User = get_user_model()
    email = "admin@example.com"
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(email=email, password="adminpassword123")
        return HttpResponse("Muvaffaqiyatli! Admin yaratildi: admin@example.com / adminpassword123")
    return HttpResponse("Admin allaqachon mavjud va tayyor!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('make-admin-now/', create_admin_quick),
    path('api/auth/login/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/accounts/', include('accounts.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('api/payroll/', include('payroll.urls')),
]
