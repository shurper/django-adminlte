import random
from .models import OTP
from celery import shared_task

def generate_otp():
    return str(random.randint(100000, 999999))

@shared_task
def send_otp(user):
    otp = generate_otp()
    OTP.objects.create(user=user, code=otp)
    # Настройте реальную отправку через WhatsApp или Telegram
    print(f"OTP для {user.phone}: {otp}")  # Замените на реальную отправку
    return otp
