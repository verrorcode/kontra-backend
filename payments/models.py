from django.db import models
from dashboard.models import SaaSPlan, UserProfile, User
from django.core.validators import MinValueValidator

class FinanceTransaction(models.Model):
    PURCHASE_TYPE_CHOICES = [
        ('credits', 'Credits'),
        ('plan', 'Plan'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=10, default="USD")  # Added for currency handling
    transaction_date = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)
    plan = models.ForeignKey(SaaSPlan, on_delete=models.SET_NULL, null=True, blank=True)
    successful = models.BooleanField(default=True)
    purchase_type = models.CharField(max_length=50, choices=PURCHASE_TYPE_CHOICES)
    plan_identifier = models.CharField(max_length=255, null=True, blank=True)

    def apply_transaction(self):
        try:
            profile = UserProfile.objects.get(user=self.user)

            if self.purchase_type == 'plan' and self.plan:
                profile.saas_plan = self.plan
                profile.plan_start_date = self.transaction_date
                profile.plan_end_date = self.transaction_date + self.plan.duration  # Assuming duration is timedelta
                profile.save()
            elif self.purchase_type == 'credits':
                profile.recharged_credits = getattr(profile, 'recharged_credits', 0) + self.amount
                profile.save()

        except UserProfile.DoesNotExist:
            # Log the error instead of creating a new profile
            raise ValueError("UserProfile does not exist for this user.")
