from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Attendance(models.Model):
    """
    Bitta xodimning bitta kunlik davomat (tabel) yozuvi.
    (employee, date) juftligi unique - bitta xodimga bitta kunda faqat bitta yozuv.
    """

    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Ishda bo\'ldi'
        ABSENT = 'ABSENT', 'Kelmadi'
        SICK = 'SICK', 'Kasallik varaqasi'
        HOLIDAY = 'HOLIDAY', 'Dam olish/bayram'

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Xodim',
    )
    date = models.DateField(verbose_name='Sana')
    hours_worked = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        verbose_name='Ishlangan soatlar',
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PRESENT,
        verbose_name='Holati',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Davomat yozuvi'
        verbose_name_plural = 'Davomat yozuvlari'
        constraints = [
            models.UniqueConstraint(
                fields=['employee', 'date'], name='unique_employee_date_attendance'
            )
        ]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['employee', 'date']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} ({self.get_status_display()})"

    def clean(self):
        # ABSENT bo'lsa hours_worked avtomat 0 bo'lishi shart (biznes-qoida)
        if self.status == self.Status.ABSENT:
            self.hours_worked = Decimal('0.00')
        if self.hours_worked < 0:
            raise ValidationError("Ishlangan soat manfiy bo'la olmaydi.")
        if self.hours_worked > 24:
            raise ValidationError("Bir kunda 24 soatdan ortiq ishlash mumkin emas.")

    def save(self, *args, **kwargs):
        # ABSENT holatida hours_worked har doim 0 bo'lishini kafolatlaymiz
        if self.status == self.Status.ABSENT:
            self.hours_worked = Decimal('0.00')
        self.full_clean(exclude=None)
        super().save(*args, **kwargs)
