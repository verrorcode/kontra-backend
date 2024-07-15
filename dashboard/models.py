
from django.db import models
from django.contrib.auth.models import User
import datetime
from django.utils import timezone
class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    folder = models.ForeignKey(Folder, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(default=timezone.now, blank=True)

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)  # 'user' or 'bot'
    timestamp = models.DateTimeField(auto_now_add=True)
