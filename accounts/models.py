from decimal import Decimal

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Email orqali foydalanuvchi yaratish uchun custom manager."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email manzil kiritilishi shart")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('role', User.Role.EMPLOYEE)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.HR)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser is_staff=True bo\'lishi kerak.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser is_superuser=True bo\'lishi kerak.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Tizimning yagona foydalanuvchi modeli.
    Ham HR Admin, ham oddiy Xodim shu model orqali ifodalanadi (role maydoni orqali farqlanadi).
    """

    class Role(models.TextChoices):
        HR = 'HR', 'HR Admin'
        EMPLOYEE = 'EMPLOYEE', 'Xodim'

    email = models.EmailField(unique=True, verbose_name='Email manzil')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon raqami')

    full_name = models.CharField(max_length=255, verbose_name="To'liq ism-familiya")
    position = models.CharField(
        max_length=150, blank=True, verbose_name='Lavozimi',
        help_text="Masalan: Frontend Dasturchi, Sotuvchi"
    )
    department = models.CharField(max_length=150, blank=True, verbose_name="Bo'limi")

    hourly_rate = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Soatbay stavka (so\'m)',
        help_text="Bir soatlik ish haqi miqdori"
    )

    role = models.CharField(
        max_length=10, choices=Role.choices, default=Role.EMPLOYEE, verbose_name='Roli'
    )

    is_active = models.BooleanField(default=True, verbose_name='Faolmi')
    is_staff = models.BooleanField(default=False, verbose_name='Admin panelga kirish huquqi')

    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='Ishga qabul qilingan sana')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.get_role_display()})"

    @property
    def is_hr(self):
        return self.role == self.Role.HR
