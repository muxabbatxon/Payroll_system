from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone

from accounts.models import User
from attendance.models import Attendance
from .models import Payroll


def calculate_payroll_for_employee(employee: User, month: int, year: int) -> Payroll:
    """
    Bitta xodim uchun berilgan oy/yil bo'yicha oylikni hisoblaydi va Payroll
    yozuvini yaratadi yoki yangilaydi (upsert).

    Algoritm (TZ 4.2 bandiga muvofiq):
    1-qadam: Xodimning shu oydagi barcha Attendance yozuvlaridan hours_worked
             yig'indisi topiladi (SUM).
    2-qadam: Jami soat x hourly_rate = Net Salary.
    3-qadam: Natija Payroll jadvaliga saqlanadi/yangilanadi.

    Barcha hisob-kitoblar Decimal turida amalga oshiriladi - Float ishlatilmaydi,
    shuning uchun pul miqdorlarida yaxlitlash xatoligi bo'lmaydi.
    """
    aggregation = Attendance.objects.filter(
        employee=employee, date__year=year, date__month=month,
    ).aggregate(total=Sum('hours_worked'))

    total_hours = aggregation['total'] or Decimal('0.00')
    total_hours = Decimal(total_hours).quantize(Decimal('0.01'))

    hourly_rate = employee.hourly_rate or Decimal('0.00')

    net_salary = (total_hours * hourly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    payroll, _created = Payroll.objects.update_or_create(
        employee=employee, month=month, year=year,
        defaults={
            'total_hours': total_hours,
            'hourly_rate_snapshot': hourly_rate,
            'net_salary': net_salary,
        },
    )
    return payroll


def calculate_payroll_bulk(month: int, year: int, employee_ids=None):
    """
    Berilgan oy uchun bir nechta (yoki barcha faol) xodimlarning oyligini hisoblaydi.
    Har bir xodim uchun sikl aylanadi (TZ da tasvirlangan algoritm).
    """
    employees_qs = User.objects.filter(role=User.Role.EMPLOYEE, is_active=True)
    if employee_ids:
        employees_qs = employees_qs.filter(id__in=employee_ids)

    results = []
    for employee in employees_qs:
        payroll = calculate_payroll_for_employee(employee, month, year)
        results.append(payroll)
    return results
