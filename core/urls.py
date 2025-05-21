from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('', include('home.urls')),
    path("admin/", admin.site.urls),
    path("", include('admin_adminlte.urls')),
    path('wildberries/', include('wildberries.urls'), name='wildberries'),
    path('notification/', include('notification.urls'), name='notification'),
    path('tradingpool/', include('tradingpool.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Добавляем статические маршруты отдельно
if settings.DEBUG:  # Добавляем только в режиме разработки, т.к. в продакшне для этого будет использоваться Nginx (это временное, т.к. на разработке тоже нужно так)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
