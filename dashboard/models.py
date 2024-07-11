
from django.db import models
from django.contrib.auth.models import User

class Folder(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Document(models.Model):
    file = models.FileField(upload_to='documents/')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
