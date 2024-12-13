from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dj_rest_auth.views import PasswordResetConfirmView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import CustomEmailConfirmView, FacebookLogin, GoogleLogin, CustomPasswordResetView
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import PasswordResetView
from django.urls import re_path
from django.contrib.auth.views import PasswordResetConfirmView as DjangoPasswordResetConfirmView
# from dj_rest_auth.registration.views import VerifyEmailView

urlpatterns = [
    # JWT Token Authentication
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Login
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refresh token
    
    # Password Reset
    path('password-reset-confirm/<uid>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/passwordreset/', CustomPasswordResetView.as_view(), name='password_reset'),
  
    # Admin site
    path('admin/', admin.site.urls),

    # Custom Email Confirm for user registration
    path('api/auth/registration/account-confirm-email/<str:key>/', CustomEmailConfirmView.as_view(), name='account_confirm_email'),

    # Default auth routes (login, logout, etc.)
    path('api/auth/', include('dj_rest_auth.urls')),  # For login, logout, password reset, etc.
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/social/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/social/facebook/', FacebookLogin.as_view(), name='facebook_login'),  # Facebook social login

    path('accounts/', include('allauth.urls')),
    # Include app URLs for the dashboard and payment features
    path('', include('dashboard.urls')),
    path('', include('payments.urls')),
]

# Serving media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
