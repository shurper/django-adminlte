from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, OTP
from .serializers import UserSerializer
from .utils import send_otp
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


@permission_classes([AllowAny])
class LoginView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({'message': 'User not found'}, status=status.HTTP_226_IM_USED)
        otp = send_otp(user)
        return Response({'message': 'OTP sent'})



# class RegisterView(APIView):
#     def post(self, request):
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             user = serializer.save()
#             send_otp(user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_206_PARTIAL_CONTENT)

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                if not send_otp(user):
                    return Response({'error': 'Не удалось отправить OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_206_PARTIAL_CONTENT)



# class OTPVerificationView(APIView):
#     def post(self, request):
#         phone = request.data.get('phone')
#         code = request.data.get('otp')
#
#         user = User.objects.filter(phone=phone).first()
#         if not user:
#             return Response({'message': 'User not found'}, status=status.HTTP_204_NO_CONTENT)
#
#         otp = OTP.objects.filter(user=user, code=code).first()
#
#         # Проверка на корректность и срок действия OTP
#         if not otp or otp.created_at < now() - timedelta(minutes=10):
#             return Response({'message': 'Invalid or expired OTP'}, status=status.HTTP_204_NO_CONTENT)
#
#         # Успешная верификация
#         otp.delete()  # Удаляем OTP после использования
#         return Response({'message': 'OTP verified', 'user_id': user.id})


# class OTPVerificationView(APIView):
#     def post(self, request):
#         phone = request.data.get('phone')
#         code = request.data.get('otp')
#
#         # Поиск пользователя по номеру телефона
#         user = User.objects.filter(phone=phone).first()
#         if not user:
#             return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)
#
#         # Проверка OTP
#         otp = OTP.objects.filter(user=user, code=code).first()
#         if not otp:
#             return Response({'message': 'Пароль указан неверно'}, status=status.HTTP_400_BAD_REQUEST)
#
#         if otp.created_at < timezone.now() - timedelta(minutes=10):
#             return Response({'message': 'Пароль указан неверно или просрочен'}, status=status.HTTP_400_BAD_REQUEST)
#
#         # Удаление OTP после успешной проверки
#         otp.delete()
#
#         # Генерация токенов
#         refresh = RefreshToken.for_user(user)
#         access_token = str(refresh.access_token)
#
#         # Возврат токенов клиенту
#         return Response({
#             'message': 'Пароль успешно верифицирован',
#             'access': access_token,
#             'refresh': str(refresh)
#         }, status=status.HTTP_200_OK)



class OTPVerificationView(APIView):
    def post(self, request):
        phone = request.data.get('phone')
        code = request.data.get('otp')

        # Поиск пользователя по номеру телефона
        user = User.objects.filter(phone=phone).first()
        if not user:
            return Response({'message': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Поиск OTP для этого пользователя
        otp = OTP.objects.filter(user=user).first()
        if not otp:
            return Response({'message': 'OTP не найден'}, status=status.HTTP_400_BAD_REQUEST)

        # Увеличиваем количество попыток
        otp.attempts += 1
        otp.save()

        # Проверка на количество попыток
        if otp.attempts > 3:
            otp.delete()  # Удаляем OTP после 3 попыток
            return Response({'message': 'Попытки ввода пароля исчерпаны.'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на срок действия кода
        if otp.created_at < timezone.now() - timedelta(minutes=10):
            otp.delete()  # Удаляем OTP, если он просрочен
            return Response({'message': 'Пароль указан неверно или просрочен'}, status=status.HTTP_400_BAD_REQUEST)

        # Проверка на правильность пароля
        if otp.code != code:
            return Response({'message': 'Пароль указан неверно'}, status=status.HTTP_400_BAD_REQUEST)

        # Удаление OTP после успешной проверки
        otp.delete()

        # Генерация токенов
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Возврат токенов клиенту
        return Response({
            'message': 'Пароль успешно верифицирован',
            'access': access_token,
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def main_page(request):
    return Response({'message': 'Welcome to the main page!', 'user': request.user.nickname})