from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total credits (base + recharged)
    recharged_credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Track recharged credits
    saas_plan = models.ForeignKey('SaaSPlan', on_delete=models.SET_NULL, null=True, blank=True)
    plan_start_date = models.DateTimeField(null=True, blank=True)
    plan_end_date = models.DateTimeField(null=True, blank=True)
    is_plan_active = models.BooleanField(default=False)
    total_documents_uploaded = models.IntegerField(default=0)

    @property
    def total_storage_used(self):
        total_storage = self.user.document_set.aggregate(total=models.Sum('file_size'))['total']
        return total_storage if total_storage else 0.0

    @property
    def base_credits(self):
        # Credits from the active plan
        return self.saas_plan.credits if self.saas_plan else 0

    @property
    def total_credits(self):
        # Sum of base plan credits and recharged credits
        return self.base_credits + self.recharged_credits

    def save(self, *args, **kwargs):
        if self.saas_plan:
            self.saas_plan.set_plan_attributes()

            if not self.plan_start_date:
                self.plan_start_date = timezone.now()
                self.plan_end_date = self.plan_start_date + timedelta(days=30)

            if self.plan_end_date and self.plan_end_date > timezone.now():
                self.is_plan_active = True
            else:
                self.is_plan_active = False

        # Recalculate the total credits before saving
        self.credits = self.total_credits

        super().save(*args, **kwargs)


class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    folder = models.ForeignKey('Folder', on_delete=models.SET_NULL, null=True, blank=True)
    file_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cloudflare_link = models.URLField(max_length=500, null=True, blank=True)  # New field for storing the Cloudflare link

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update the total documents uploaded in UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.total_documents_uploaded = Document.objects.filter(user=self.user).count()
        profile.save()

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

class SaaSPlan(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    max_storage_mb = models.IntegerField()  # Maximum storage allowed in MB
    price_per_month = models.DecimalField(max_digits=6, decimal_places=2)  # Monthly price
    max_queries = models.IntegerField()  # Maximum number of queries allowed per month

class FinanceTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    plan = models.ForeignKey(SaaSPlan, on_delete=models.SET_NULL, null=True, blank=True)
    successful = models.BooleanField(default=True)
    purchase_type = models.CharField(max_length=50, choices=[('credits', 'Credits'), ('plan', 'Plan')])
    plan_identifier = models.CharField(max_length=255, null=True, blank=True)

    def apply_transaction(self):
        profile = self.user.userprofile

        # Handle plan purchases
        if self.purchase_type == 'plan' and self.plan:
            profile.saas_plan = self.plan
            profile.recharged_credits = 0  # Reset recharged credits on plan change
            profile.save()

        # Handle credit recharges
        elif self.purchase_type == 'credits':
            profile.recharged_credits += self.amount
            profile.save()
