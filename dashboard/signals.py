# signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile, SaaSPlan
from django.contrib.auth.models import User
from datetime import datetime, timedelta
@receiver(user_logged_in)
def create_user_profile_on_first_login(sender, request, user, **kwargs):
    """
    This function will create a UserProfile for the user upon their first login
    and assign them to the free SaaS plan tier.
    """
    if not hasattr(user, 'userprofile'):  # Only create if the profile does not exist
        # Get or create the 'Free' plan
        free_plan, created = SaaSPlan.objects.get_or_create(name='free')
        if created:
            free_plan.set_plan_attributes()

        # Create UserProfile
        user_profile = UserProfile.objects.create(
            user=user,
            saas_plan=free_plan,
            credits=free_plan.credits,  # Assuming free plan has credits defined
            recharged_credits=0.0,  # Initially no recharged credits
            plan_start_date=timezone.now(),
            plan_end_date=timezone.now() + timedelta(days=30),  # Free plan for 30 days
        )
        user_profile.save()
