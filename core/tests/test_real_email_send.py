from django.core.mail import send_mail
from django.test import TestCase
from core import settings

# python manage.py test core.tests.test_real_email_send.RealEmailSendTest.test_real_email_send
class RealEmailSendTest(TestCase):
    def test_real_email_send(self):
        # Настоящий получатель, на который вы хотите отправить тестовый email
        recipient_email = settings.DEFAULT_TO_TEST_EMAIL

        # Вывод текущих настроек SMTP
        print("Текущие настройки SMTP:")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print(f"recipient_email: {recipient_email}")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")

        try:
            send_mail(
                subject="Тестовая отправка реального письма",
                message="Это тестовое сообщение для проверки SMTP-сервера.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Ошибка при отправке email: {e}")

        # Визуально проверьте, что письмо пришло в ваш почтовый ящик
        print(f"Email отправлен на {recipient_email}. Проверьте почту для подтверждения.")