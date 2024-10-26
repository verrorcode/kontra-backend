"""Kontra URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
""" 

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from dashboard.routing import websocket_urlpatterns 
from accounts.views import CustomEmailVerificationView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [ 
    # path('', include('django.contrib.auth.urls')),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    
    path("password-reset/confirm/<uidb64>/<token>/",
       TemplateView.as_view(template_name="password_reset_confirm.html"),
       name='password_reset_confirm'),
    path('admin/', admin.site.urls),
    # path('api/auth/password/reset/', PasswordResetView.as_view(), name='password_reset_confirm'),

    path('api/auth/registration/account-confirm-email/<str:key>/', CustomEmailVerificationView.as_view(), name='account_confirm_email'),
 
    path('api/auth/', include('dj_rest_auth.urls')),  # For login, logout, password reset, etc.
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('', include('dashboard.urls')),
   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# WebSocket routing
application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # Your WebSocket URL patterns defined in myapp.routing
        )
    ),
    # Other protocol configurations if needed
})