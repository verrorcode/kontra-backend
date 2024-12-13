from django.contrib import admin
from .models import UserProfile, Folder, Document, ChatMessage, SaaSPlan
from payments.models import FinanceTransaction
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Folder)
admin.site.register(Document)
admin.site.register(ChatMessage)
admin.site.register(SaaSPlan)
admin.site.register(FinanceTransaction)
