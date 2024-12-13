import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .models import FinanceTransaction
from dashboard.models import SaaSPlan, UserProfile, User
from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.utils import timezone
from dashboard.models import UserProfile, SaaSPlan
from .models import FinanceTransaction

logger = logging.getLogger(__name__)


class PayPalWebhookView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def post(self, request):
        try:
            payload = request.body.decode('utf-8')
            logger.info(f"Webhook payload: {payload}")
            event_body = request.data
            event_type = event_body.get('event_type')
            resource = event_body.get('resource')
            subscription_id = resource.get('id')
            user_id = resource.get('custom_id')  # Assuming custom_id is the user's ID

            # Fetch user and check for existing transaction for this subscription ID
            user = User.objects.get(id=user_id)
            existing_transaction = FinanceTransaction.objects.filter(plan_identifier=subscription_id).first()

            # Prevent duplicate processing for the same subscription_id
            if existing_transaction:
                logger.info(f"Duplicate subscription event received for subscription {subscription_id}. Skipping processing.")
                return Response({'status': 'success'}, status=200)

            # Handling One-Time Payment (CHECKOUT.ORDER.APPROVED)
            if event_type == 'CHECKOUT.ORDER.APPROVED':
                transaction_id = resource['id']
                amount = resource['purchase_units'][0]['amount']['value']
                currency = resource['purchase_units'][0]['amount']['currency_code']

                FinanceTransaction.objects.create(
                    user=user,
                    amount=amount,
                    currency=currency,
                    description="One-time payment",
                    successful=True,
                    purchase_type="credits",
                    plan_identifier=transaction_id,
                    transaction_date=timezone.now()
                )
                logger.info(f"One-time payment processed for user {user.id}.")

            # Handling Subscription Creation (BILLING.SUBSCRIPTION.CREATED)
            elif event_type == 'BILLING.SUBSCRIPTION.CREATED':
                plan_id = resource.get('plan_id')
                saas_plan = SaaSPlan.objects.get(paypal_plan_id=plan_id)  # Match with `paypal_plan_id`

                # Update user profile with subscription details
                user_profile = UserProfile.objects.get(user=user)
                user_profile.saas_plan = saas_plan
                user_profile.plan_start_date = timezone.now()
                user_profile.plan_end_date = user_profile.plan_start_date + timedelta(days=30 if saas_plan.duration == 'monthly' else 365)
                existing_credits = user_profile.credits 
                user_profile.credits = saas_plan.credits + existing_credits  # Update with plan credits
                user_profile.save()

                # Add a record in the FinanceTransaction model
                FinanceTransaction.objects.create(
                    user=user,
                    amount=saas_plan.price,  # Assuming `price` is a field in SaaSPlan
                    currency="USD",  # Replace with actual currency if dynamic
                    description="Subscription created",
                    successful=True,
                    purchase_type="plan",
                    plan_identifier=subscription_id,
                    transaction_date=timezone.now()
                )
                logger.info(f"Subscription created for user {user.id} with plan {saas_plan.name}.")

            # Handling Subscription Activation (BILLING.SUBSCRIPTION.ACTIVATED)
            elif event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
                if existing_transaction:
                    logger.info(f"Subscription {subscription_id} has already been activated. Skipping processing.")
                    return Response({'status': 'success'}, status=200)

                # Fetch details from billing_info and use for transaction
                billing_info = resource.get('billing_info', {})
                amount = billing_info.get('last_payment', {}).get('amount', {}).get('value', 0.0)
                currency = billing_info.get('last_payment', {}).get('amount', {}).get('currency_code', 'USD')
                saas_plan = SaaSPlan.objects.get(paypal_plan_id=resource.get('plan_id'))

                # Store the transaction for subscription activation
                FinanceTransaction.objects.create(
                    user=user,
                    amount=amount,
                    currency=currency,
                    description="Subscription activation",
                    successful=True,
                    purchase_type="plan",
                    plan_identifier=subscription_id,
                    transaction_date=timezone.now()
                )

                # Update the user's profile with the subscription details
                user_profile = UserProfile.objects.get(user=user)
                previous_credits = user_profile.recharged_credits
                user_profile.saas_plan = saas_plan
                user_profile.plan_start_date = timezone.now()
                existing_credits = user_profile.credits 
                user_profile.credits = saas_plan.credits + existing_credits

                if saas_plan.duration == 'monthly':
                    user_profile.plan_end_date = user_profile.plan_start_date + timedelta(days=30)
                elif saas_plan.duration == 'yearly':
                    user_profile.plan_end_date = user_profile.plan_start_date + timedelta(days=365)

                user_profile.save()

                # Notify the user about updated credits
                self.send_credits_updated_email(user, previous_credits, saas_plan.credits)
                logger.info(f"Subscription activated for user {user.id} with plan {saas_plan.name}.")

            return Response({'status': 'success'}, status=200)

        except Exception as e:
            logger.error(f"Error processing PayPal webhook: {str(e)}")
            return Response({'error': 'Webhook processing failed'}, status=400)

    def send_credits_updated_email(self, user, previous_credits, new_plan_credits):
        subject = "Your Credits Have Been Updated with Your New Plan"
        message = (
            f"Dear {user.username},\n\n"
            f"Your plan has been successfully upgraded. We have updated your credits to reflect the new plan, which now includes {new_plan_credits} credits.\n\n"
            f"Your previous recharged credits of {previous_credits} have not been affected and remain available for use.\n\n"
            f"Thank you for your continued support.\n\n"
            f"Best regards,\n"
            f"Team Kontra"
        )
        send_mail(subject, message, 'vaibhav@admirian.com', [user.email])
