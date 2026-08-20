from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Email + parol orqali login qilish uchun JWT serializer."""

    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'full_name': self.user.full_name,
            'email': self.user.email,
            'role': self.user.role,
        }
        return data


class UserListSerializer(serializers.ModelSerializer):
    """Xodimlar ro'yxati (jadval) uchun qisqartirilgan serializer."""

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'position',
            'department', 'hourly_rate', 'role', 'is_active', 'date_joined',
        ]


class UserCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Yangi xodim qo'shish / mavjud xodimni tahrirlash uchun serializer.
    Faqat HR Admin foydalana oladi (permission darajasida tekshiriladi).
    """

    password = serializers.CharField(
        write_only=True, required=False, validators=[validate_password],
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'position', 'department',
            'hourly_rate', 'role', 'is_active', 'password',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', None) or User.objects.make_random_password()
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MeSerializer(serializers.ModelSerializer):
    """Joriy foydalanuvchi (/me) uchun serializer - o'zgartirib bo'lmaydigan maydonlar bilan."""

    class Meta:
        model = User
        fields = [
            'id', 'full_name', 'email', 'phone', 'position',
            'department', 'hourly_rate', 'role',
        ]
        read_only_fields = fields
