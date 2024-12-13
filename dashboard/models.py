from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from . import variables
from django.core.validators import MinValueValidator
from decimal import Decimal


class SaaSPlan(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    DURATION_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES)
    max_storage_mb = models.IntegerField(default=10)  # Maximum storage allowed in MB
    price = models.DecimalField(default=0, max_digits=6, decimal_places=2)  # Total price (monthly or yearly)
    max_queries = models.IntegerField(default=0)  # Maximum number of queries allowed per month
    max_documents = models.IntegerField(default=0)  # Maximum number of documents allowed
    duration = models.CharField(max_length=7, choices=DURATION_CHOICES, default='monthly')  # 'monthly' or 'yearly'
    paypal_plan_id = models.CharField(max_length=100, null=True, blank=True, unique=True)  # PayPal Plan ID

    class Meta:
        unique_together = ('name', 'duration')
        
    def set_plan_attributes(self):
        # Set attributes based on the plan's name and duration
        if self.name == 'free':
            self.max_storage_mb = variables.SaasPlanStorage.Free
            self.max_queries = variables.SaasPlanQueries.Free
            self.max_documents = variables.SaasPlanDocuments.Free
            self.price = variables.SaasPlanPricing.Free
        elif self.name == 'basic':
            if self.duration == 'monthly':
                self.max_storage_mb = variables.SaasPlanStorage.Basic
                self.max_queries = variables.SaasPlanQueries.Basic
                self.max_documents = variables.SaasPlanDocuments.Basic
                self.price = variables.SaasPlanPricing.Basic
            elif self.duration == 'yearly':
                self.max_storage_mb = variables.SaasPlanStorage.Basic * 12
                self.max_queries = variables.SaasPlanQueries.Basic * 12
                self.max_documents = variables.SaasPlanDocuments.Basic * 12
                self.price = variables.SaasPlanPricing.BasicYearly
        elif self.name == 'standard':
            if self.duration == 'monthly':
                self.max_storage_mb = variables.SaasPlanStorage.Standard
                self.max_queries = variables.SaasPlanQueries.Standard
                self.max_documents = variables.SaasPlanDocuments.Standard
                self.price = variables.SaasPlanPricing.Standard
            elif self.duration == 'yearly':
                self.max_storage_mb = variables.SaasPlanStorage.Standard * 12
                self.max_queries = variables.SaasPlanQueries.Standard * 12
                self.max_documents = variables.SaasPlanDocuments.Standard * 12
                self.price = variables.SaasPlanPricing.StandardYearly
        elif self.name == 'premium':
            if self.duration == 'monthly':
                self.max_storage_mb = variables.SaasPlanStorage.Premium
                self.max_queries = variables.SaasPlanQueries.Premium
                self.max_documents = variables.SaasPlanDocuments.Premium
                self.price = variables.SaasPlanPricing.Premium
            elif self.duration == 'yearly':
                self.max_storage_mb = variables.SaasPlanStorage.Premium * 12
                self.max_queries = variables.SaasPlanQueries.Premium * 12
                self.max_documents = variables.SaasPlanDocuments.Premium * 12
                self.price = variables.SaasPlanPricing.PremiumYearly

    def save(self, *args, **kwargs):
        # Ensure plan attributes are set before saving
        self.set_plan_attributes()
        super().save(*args, **kwargs)

    @property
    def credits(self):
        # Credits calculation logic
        if self.name == 'free':
            return variables.SaasPlanCredits.Free
        elif self.name == 'basic':
            if self.duration == 'monthly':
                return variables.SaasPlanCredits.Basic
            elif self.duration == 'yearly':
                return variables.SaasPlanCredits.Basic * 12
        elif self.name == 'standard':
            if self.duration == 'monthly':
                return variables.SaasPlanCredits.Standard
            elif self.duration == 'yearly':
                return variables.SaasPlanCredits.Standard * 12
        elif self.name == 'premium':
            if self.duration == 'monthly':
                return variables.SaasPlanCredits.Premium
            elif self.duration == 'yearly':
                return variables.SaasPlanCredits.Premium * 12
        return 0

    def __str__(self):
        return f"{self.name} - {self.duration.capitalize()} Plan"

    def set_plan_from_paypal_id(self, paypal_plan_id):
        # Mapping PayPal Plan IDs to the corresponding plans
        if paypal_plan_id == variables.SaasPlanPaypalMontly.Basic:
            self.name = 'basic'
            self.duration = 'monthly'
        elif paypal_plan_id == variables.SaasPlanPaypalMontly.Standard:
            self.name = 'standard'
            self.duration = 'monthly'
        elif paypal_plan_id == variables.SaasPlanPaypalMontly.Premium:
            self.name = 'premium'
            self.duration = 'monthly'
        elif paypal_plan_id == variables.SaasPlanPaypalYearly.Basic:
            self.name = 'basic'
            self.duration = 'yearly'
        elif paypal_plan_id == variables.SaasPlanPaypalYearly.Standard:
            self.name = 'standard'
            self.duration = 'yearly'
        elif paypal_plan_id == variables.SaasPlanPaypalYearly.Premium:
            self.name = 'premium'
            self.duration = 'yearly'
        else:
            # Handle unknown plan ID or fallback (optional)
            self.name = 'free'
            self.duration = 'monthly'

        self.set_plan_attributes()  # Call to update plan attributes based on the name and duration
        self.paypal_plan_id = paypal_plan_id  # Save the PayPal Plan ID
        self.save()


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
    name = models.CharField(max_length=255, null=True)

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)
    folder = models.ForeignKey('Folder', on_delete=models.SET_NULL, null=True, blank=True)
    file_size = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    cloudflare_link = models.URLField(max_length=500, null=True, blank=True)
    embeddings_stored = models.BooleanField(default=False)
    file_key = models.CharField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Calculate the file size in MB if file is provided
        if self.file:
            self.file_size = Decimal(self.file.size) / (1024 * 1024)  # Size in MB

        super().save(*args, **kwargs)

        # Update the UserProfile's total_documents_uploaded and total_storage_used
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.total_documents_uploaded = Document.objects.filter(user=self.user).count()
        profile.update_total_storage_used()  # Assumes this method calculates and updates storage used
        profile.save()

    def __str__(self):
        return f"{self.file.name} ({self.user.username})"

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('bot', 'Bot'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

