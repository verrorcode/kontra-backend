from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from . import variables
from django.core.validators import MinValueValidator


class SaaSPlan(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    max_storage_mb = models.IntegerField(default=10)  # Maximum storage allowed in MB
    price_per_month = models.DecimalField(default=0, max_digits=6, decimal_places=2)  # Monthly price
    max_queries = models.IntegerField(default=0)  # Maximum number of queries allowed per month
    max_documents = models.IntegerField(default=0)  # Maximum number of documents allowed

    def set_plan_attributes(self):
        if self.name == 'free':
            self.max_storage_mb = variables.SaasPlanStorage.Free
            self.max_queries = variables.SaasPlanDocuments.Free
            self.max_documents = variables.SaasPlanDocuments.Free
            self.price_per_month = variables.SaasPlanPricing.Free
        elif self.name == 'basic':
            self.max_storage_mb = variables.SaasPlanStorage.Basic
            self.max_queries = variables.SaasPlanDocuments.Basic
            self.max_documents = variables.SaasPlanDocuments.Basic
            self.price_per_month = variables.SaasPlanPricing.Basic
        elif self.name == 'standard':
            self.max_storage_mb = variables.SaasPlanStorage.Standard
            self.max_queries = variables.SaasPlanDocuments.Standard
            self.max_documents = variables.SaasPlanDocuments.Standard
            self.price_per_month = variables.SaasPlanPricing.Standard
        elif self.name == 'premium':
            self.max_storage_mb = variables.SaasPlanStorage.Premium
            self.max_queries = variables.SaasPlanDocuments.Premium
            self.max_documents = variables.SaasPlanDocuments.Premium
            self.price_per_month = variables.SaasPlanPricing.Premium

        # Ensure the plan attributes are valid
        self.save()

    @property
    def credits(self):
        if self.name == 'free':
            return variables.SaasPlanCredits.Free
        elif self.name == 'basic':
            return variables.SaasPlanCredits.Basic
        elif self.name == 'standard':
            return variables.SaasPlanCredits.Standard
        elif self.name == 'premium':
            return variables.SaasPlanCredits.Premium
        return 0

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    recharged_credits = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    saas_plan = models.ForeignKey(SaaSPlan, on_delete=models.SET_NULL, null=True, blank=True)
    plan_start_date = models.DateTimeField(null=True, blank=True)
    plan_end_date = models.DateTimeField(null=True, blank=True)
    is_plan_active = models.BooleanField(default=False)
    total_documents_uploaded = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    @property
    def total_storage_used(self):
        total_storage = self.user.document_set.aggregate(total=models.Sum('file_size'))['total']
        return total_storage if total_storage else 0.0

    @property
    def base_credits(self):
        return self.saas_plan.credits if self.saas_plan else 0

    @property
    def total_credits(self):
        return self.base_credits + self.recharged_credits

    def save(self, *args, **kwargs):
        if not self.saas_plan:
            free_plan, created = SaaSPlan.objects.get_or_create(name='free')
            if created:
                free_plan.set_plan_attributes()
            self.saas_plan = free_plan

        self.saas_plan.set_plan_attributes()

        if not self.plan_start_date:
            self.plan_start_date = timezone.now()
            self.plan_end_date = self.plan_start_date + timedelta(days=30)

        self.is_plan_active = self.plan_end_date and self.plan_end_date > timezone.now()
        

        super().save(*args, **kwargs)

    def update_total_storage_used(self):
        self.save()  # This will trigger the total_storage_used property


class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    folder = models.ForeignKey(Folder, on_delete=models.SET_NULL, null=True, blank=True)
    file_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cloudflare_link = models.URLField(max_length=500, null=True, blank=True)  # New field for storing the Cloudflare link
    embeddings_stored = models.BooleanField(default=False) 
    file_key = models.CharField(max_length=255, null=True, blank=True)
    def save(self, *args, **kwargs):
        # Calculate the file size before saving
        self.file_size = self.file.size / (1024 * 1024)  # Size in MB
        super().save(*args, **kwargs)

        # Update the total documents uploaded in UserProfile
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.total_documents_uploaded = Document.objects.filter(user=self.user).count()
        profile.update_total_storage_used()  # Update the total storage used
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

class FinanceTransaction(models.Model):
    PURCHASE_TYPE_CHOICES = [
        ('credits', 'Credits'),
        ('plan', 'Plan'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    transaction_date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    plan = models.ForeignKey(SaaSPlan, on_delete=models.SET_NULL, null=True, blank=True)
    successful = models.BooleanField(default=True)
    purchase_type = models.CharField(max_length=50, choices=PURCHASE_TYPE_CHOICES)
    plan_identifier = models.CharField(max_length=255, null=True, blank=True)

    def apply_transaction(self):
        profile, created = UserProfile.objects.get_or_create(user=self.user)

        if self.purchase_type == 'plan' and self.plan:
            profile.saas_plan = self.plan
            profile.recharged_credits = 0
            profile.save()
        elif self.purchase_type == 'credits':
            profile.recharged_credits += self.amount
            profile.save()