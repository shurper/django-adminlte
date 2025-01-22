from rest_framework import serializers
from .models import User, OTP

class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['user', 'code']


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False)

    class Meta:
        model = User
        fields = ['name', 'nickname', 'phone', 'avatar', 'messenger']

    def validate_phone(self, value):
        # Если выполняется обновление, игнорируем текущего пользователя
        if User.objects.filter(phone=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Этот номер телефона уже зарегистрирован.")
        return value

    def validate_nickname(self, value):
        # Если выполняется обновление, игнорируем текущего пользователя
        if User.objects.filter(nickname=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("Этот никнейм уже занят. Придумайте уникальное значение.")
        return value


