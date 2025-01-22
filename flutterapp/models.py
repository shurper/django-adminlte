from django.db import models

class User(models.Model):
    name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    messenger = models.CharField(
        max_length=10,
        choices=[('whatsapp', 'WhatsApp'), ('telegram', 'Telegram')]
    )
    created_at = models.DateTimeField(auto_now_add=True)

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.IntegerField(default=0)  # Количество попыток
