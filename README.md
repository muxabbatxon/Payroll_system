# HR Payroll System — Backend (Django REST Framework)

Xodimlar davomati (tabel) va oylik maoshni avtomatik hisoblash tizimining backend qismi.
TZ (texnik topshiriq) asosida to'liq ishlab chiqilgan.

## 1. Texnologiyalar

- **Python 3.12**, **Django 5.0**, **Django REST Framework 3.15**
- **SimpleJWT** — autentifikatsiya (email + parol orqali login)
- **django-filter** — filtrlash
- **PostgreSQL** (production) / **SQLite** (development, default)
- Barcha pul va soat qiymatlari uchun **`DecimalField`** ishlatilgan (Float emas!) — tiyingacha aniqlik kafolatlanadi.

## 2. Loyiha strukturasi

```
hr_payroll_system/
├── config/            # Django sozlamalari, asosiy urls.py
├── accounts/          # User modeli (HR/EMPLOYEE), login, xodimlar CRUD, dashboard
├── attendance/         # Tabel/Davomat: model, grid API, autosave (upsert)
├── payroll/            # Oylik hisoblash logikasi (services.py) va API
├── requirements.txt
├── .env.example
└── manage.py
```

## 3. O'rnatish

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # kerakli qiymatlarni to'ldiring
python manage.py migrate
python manage.py createsuperuser  # HR admin yaratish uchun (role=HR bo'lishi kerak)

python manage.py runserver
```

> Eslatma: `createsuperuser` orqali yaratilgan foydalanuvchi avtomatik `role=HR` bo'ladi.
> Oddiy xodimlarni esa HR tizimga kirgach, `/api/accounts/employees/` orqali qo'shadi.

## 4. Ma'lumotlar modellari

### User (`accounts.User`)
Custom user model, login **email** orqali amalga oshiriladi.

| Maydon | Tur | Izoh |
|---|---|---|
| email | EmailField (unique) | Login uchun |
| full_name | CharField | To'liq ism |
| position, department | CharField | Lavozim, bo'lim |
| hourly_rate | **Decimal(12,2)** | Soatbay stavka |
| role | Enum: `HR` / `EMPLOYEE` | Ruxsat darajasi |

### Attendance (`attendance.Attendance`)
| Maydon | Tur | Izoh |
|---|---|---|
| employee | FK → User | |
| date | DateField | |
| hours_worked | **Decimal(5,2)** | Status=`ABSENT` bo'lsa avtomat `0.00` |
| status | Enum: `PRESENT/ABSENT/SICK/HOLIDAY` | |

`UniqueConstraint(employee, date)` — bitta xodimga bitta kunda faqat bitta yozuv (dublikat mumkin emas).

### Payroll (`payroll.Payroll`)
| Maydon | Tur | Izoh |
|---|---|---|
| employee, month, year | FK / Int | |
| total_hours | **Decimal(8,2)** | Oy davomidagi jami soat (SUM) |
| hourly_rate_snapshot | **Decimal(12,2)** | Hisoblangan paytdagi stavka (tarixiy) |
| net_salary | **Decimal(14,2)** | `total_hours × hourly_rate` |
| is_paid | Boolean | To'landimi |

`UniqueConstraint(employee, month, year)`.

## 5. Ruxsatlar (Permissions)

- **HR** — barcha amallarni bajaradi (xodim qo'shish, tabel to'ldirish, oylikni hisoblash).
- **EMPLOYEE** — faqat **o'z** ma'lumotlarini **o'qiy** oladi (`GET`); yozish/o'zgartirish amallari `403 Forbidden` bilan rad etiladi.

Bu `accounts/permissions.py` dagi `IsHR` va `IsHRorReadOnlySelf` klasslari orqali ta'minlangan va testlangan (xodim boshqa xodim maoshini yoki tabelini o'zgartira olmaydi).

## 6. API endpointlar

### Autentifikatsiya
| Method | URL | Izoh |
|---|---|---|
| POST | `/api/auth/login/` | `{email, password}` → `{access, refresh, user}` |
| POST | `/api/auth/refresh/` | `{refresh}` → yangi `access` token |

### Accounts (HR / Xodimlar)
| Method | URL | Kim | Izoh |
|---|---|---|---|
| GET | `/api/accounts/me/` | hamma | Joriy profil |
| GET | `/api/accounts/dashboard/` | HR | Dashboard statistikasi |
| GET | `/api/accounts/employees/` | hamma | Ro'yxat (xodim faqat o'zinikini ko'radi) |
| POST | `/api/accounts/employees/` | HR | Yangi xodim qo'shish |
| PATCH/PUT | `/api/accounts/employees/{id}/` | HR | Tahrirlash |
| DELETE | `/api/accounts/employees/{id}/` | HR | O'chirish |

### Attendance (Tabel)
| Method | URL | Kim | Izoh |
|---|---|---|---|
| GET | `/api/attendance/records/?month=&year=&employee=` | hamma | Ro'yxat/filtr |
| POST | `/api/attendance/records/save_cell/` | HR | **Autosave**: bitta katak (employee+date) uchun Upsert |
| GET | `/api/attendance/records/monthly_grid/?month=4&year=2026` | hamma | Excel-simon **grid** — barcha xodim × barcha kun |

**`save_cell` misoli** (frontendda katakdan chiqilganda `onBlur` orqali yuboriladi):
```json
POST /api/attendance/records/save_cell/
{
  "employee": 5,
  "date": "2026-04-15",
  "hours_worked": 8,
  "status": "PRESENT"
}
```
Backend avval shu `(employee, date)` uchun yozuv borligini tekshiradi → bo'lsa **UPDATE**, bo'lmasa **CREATE** (Upsert). Shu sababli ikki marta jo'natilsa ham dublikat hosil bo'lmaydi.

### Payroll (Oylik hisob-kitob)
| Method | URL | Kim | Izoh |
|---|---|---|---|
| POST | `/api/payroll/calculate/` | HR | **"Oylikni hisoblash" tugmasi** — asosiy algoritm |
| GET | `/api/payroll/records/?month=&year=&employee=` | hamma | Natija jadvali |
| PATCH | `/api/payroll/records/{id}/mark_paid/` | HR | To'landi deb belgilash |

**`calculate` misoli**:
```json
POST /api/payroll/calculate/
{ "month": 4, "year": 2026 }        // employee_ids ixtiyoriy, bo'sh bo'lsa barcha faol xodimlar
```

**Hisoblash algoritmi** (`payroll/services.py`):
1. Har bir xodim uchun shu oydagi barcha `Attendance.hours_worked` yig'indisi olinadi (`SUM`, Decimal aniqlikda).
2. `net_salary = total_hours × hourly_rate` (`Decimal`, `ROUND_HALF_UP` bilan tiyingacha yaxlitlanadi).
3. Natija `Payroll` jadvaliga **upsert** qilinadi (qayta hisoblansa eskisi yangilanadi, dublikat hosil bo'lmaydi).

## 7. Sinovdan o'tkazilgan holatlar (Acceptance Criteria bo'yicha)

Loyiha smoke-test orqali quyidagilar tasdiqlandi:
- ✅ Bitta katakka ikki marta yozilganda ham bazada faqat 1 ta `Attendance` yozuvi qoladi (Upsert).
- ✅ 23.5 soat × 35 000 so'm = **822 500.00 so'm** — Decimal orqali xatosiz hisoblandi.
- ✅ `EMPLOYEE` roli `dashboard` va `save_cell` kabi HR-only endpointlarga kirishga urinsa — `403 Forbidden`.
- ✅ Xodim faqat o'zining `Payroll` yozuvlarini ko'ra oladi.

## 8. Keyingi qadamlar (frontend uchun tavsiya)

- Tabel grid uchun `GET /api/attendance/records/monthly_grid/` dan foydalanib, jadvalni React/Vue’da render qiling; har bir katak `onBlur`da `save_cell`ga yuborilsin.
- Sticky header uchun frontendda `position: sticky` CSS ishlatiladi (backend tomonidan cheklov yo'q).
