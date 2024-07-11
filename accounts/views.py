from django.shortcuts import render

from django.contrib.auth.models import AbstractUser
from django.db import models

from django.views.generic import TemplateView

class AccountEmailVerificationSentView(TemplateView):
    template_name = 'account/email/account_email_verification_sent.html'



class AccountEmailConfirmationView(TemplateView):
    template_name = 'account/email/account_confirm_email.html'
