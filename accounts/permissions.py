from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsHR(BasePermission):
    """
    Faqat HR Admin rolidagi foydalanuvchilarga ruxsat beradi.
    Xodimlar (EMPLOYEE) tarkib yaratish/o'zgartirish/o'chirish amallarini bajara olmaydi.
    """

    message = "Bu amalni faqat HR Admin bajara oladi."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'HR'
        )


class IsHRorReadOnlySelf(BasePermission):
    """
    HR Admin - barcha amallarni bajara oladi.
    Oddiy Xodim - faqat GET (read-only) so'rov yubora oladi va faqat o'ziga tegishli
    ma'lumotlarni ko'ra oladi (obyekt darajasidagi tekshiruv has_object_permission'da).
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role == 'HR':
            return True

        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'HR':
            return True
        if request.method not in SAFE_METHODS:
            return False

        owner_id = getattr(obj, 'employee_id', getattr(obj, 'id', None))
        return owner_id == request.user.id
