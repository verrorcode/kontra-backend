
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import AccountEmailVerificationSentView, AccountEmailConfirmationView
urlpatterns = [
    path('dj-rest-auth/registration/account-email-verification-sent/', AccountEmailVerificationSentView.as_view(), name='account_email_verification_sent'),
    path('dj-rest-auth/registration/account-email-confirm/<key>/', AccountEmailConfirmationView.as_view(), name='account_email_confirm'),


]