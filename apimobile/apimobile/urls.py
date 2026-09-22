from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title='Paprika Mobile API',
        default_version='v1',
        description=(
            'API мобильного приложения Paprika.\n\n'
            '**Авторизация.** 1) `POST /auth/send-code/` - получить `txn_id` и SMS-код; '
            '2) `POST /auth/check-sent-code/` - обменять код на `auth_token`; '
            '3) передавать `auth_token` заголовком `auth-token` в методах с замком. '
            'В Swagger UI нажмите **Authorize** и вставьте токен.\n\n'
            'Ошибки валидации полей запроса возвращаются как `400` со словарём '
            '`{поле: [ошибки]}`.'
        ),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('auth/', include('authentification.urls')),
    path('admin/', admin.site.urls),
    path('api/v1/piza/', include('piza.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='swagger-schema'),
    # медиа отдаёт Django и при DEBUG=False: перед ним только reverse-proxy Caddy
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]