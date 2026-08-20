from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Payroll(models.Model):
    """
    Bitta xodimning bitta oy uchun hisoblangan oylik varaqasi.
    Barcha pul va soat qiymatlari Decimal turida saqlanadi (Float taqiqlanadi -
    tiyingacha aniqlik talab qilinadi).
    """

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payrolls',
        verbose_name='Xodim',
    )
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Oy',
    )
    year = models.PositiveIntegerField(verbose_name='Yil')

    total_hours = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Jami ishlagan soatlar',
    )
    hourly_rate_snapshot = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Hisoblangan paytdagi soatbay stavka',
        help_text="Kelajakda xodim stavkasi o'zgarsa ham, o'sha oy uchun tarixiy stavka saqlanib qoladi.",
    )
    net_salary = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Qo\'lga tegadigan summa (Net Salary)',
    )

    is_paid = models.BooleanField(default=False, verbose_name='To\'landimi')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='To\'langan sana')

    calculated_at = models.DateTimeField(auto_now=True, verbose_name='Hisoblangan sana')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Oylik hisob-kitob'
        verbose_name_plural = 'Oylik hisob-kitoblar'
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'month', 'year'], name='unique_employee_month_year_payroll'
            )
        ]
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.employee.full_name} - {self.month}/{self.year}: {self.net_salary}"
