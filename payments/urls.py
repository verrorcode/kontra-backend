# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('paypal-webhook/', views.PayPalWebhookView.as_view(), name='paypal_webhook'),
]