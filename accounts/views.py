from allauth.account.views import ConfirmEmailView
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import render, redirect
from Kontra.settings import SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI, FLUTTERFLOW_FRONTEND_URL
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.google.provider import GoogleProvider
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response
from rest_framework import status
from allauth.socialaccount.providers import registry
from allauth.socialaccount.providers.base import ProviderAccount
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework import status
from django.core.mail import send_mail
import requests
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
import jwt 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from dj_rest_auth.views import PasswordResetView
from django.contrib.auth.forms import PasswordResetForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.utils.html import strip_tags
# Custom view for email confirmation
class CustomEmailConfirmView(ConfirmEmailView):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if response.status_code == 200:
            messages.success(request, _("Your email has been confirmed successfully!"))
            return render(request, 'email_confirm.html')
        else:
            messages.error(request, _("The confirmation link is invalid or has expired."))
            return redirect('account_login')
# accounts/views.py
from dj_rest_auth.views import PasswordResetView
from .serializers import CustomPasswordResetSerializer

class CustomPasswordResetView(PasswordResetView):
    serializer_class = CustomPasswordResetSerializer

# FACEBOOK AUTHENTICATION
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.oauth2.client import OAuth2Client  # Import this class


# Custom OAuth2Client to override the problematic behavior
class CustomOAuth2Client(OAuth2Client):
    def __init__(self, *args, **kwargs):
        # Remove scope_delimiter from kwargs if it exists
        kwargs.pop('scope_delimiter', None)
        super().__init__(*args, **kwargs)

# Custom Facebook OAuth Adapter
class CustomFacebookOAuth2Adapter(FacebookOAuth2Adapter):
    client_class = CustomOAuth2Client  # Use our custom client class

    def get_provider(self):
        provider = super().get_provider()
        provider.get_scope = lambda *args, **kwargs: provider.get_default_scope()  # Avoid scope conflicts
        return provider

# Facebook Login View
class FacebookLogin(SocialLoginView):
    adapter_class = CustomFacebookOAuth2Adapter  # Use the custom adapter
    client_class = CustomOAuth2Client  # Explicitly define the custom client
    callback_url = settings.SOCIAL_AUTH_FACEBOOK_OAUTH2_REDIRECT_URI




# GOOGLE AUTHENTICATION


class CustomGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    access_token_url = 'https://oauth2.googleapis.com/token'
    authorize_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    profile_url = 'https://www.googleapis.com/oauth2/v2/userinfo'

    def get_provider(self):
        provider = super().get_provider()
        provider.get_scope = lambda *args, **kwargs: provider.get_default_scope()
        return provider

    def complete_login(self, request, app, token, response, **kwargs):
        try:
            # First try to get user info from access token
            resp = requests.get(
                self.profile_url,
                headers={'Authorization': f'Bearer {token.token}'}
            )
            resp.raise_for_status()
            extra_data = resp.json()
            
            return self.get_provider().sociallogin_from_response(request, extra_data)
            
        except Exception as e:
            print(f"Error getting profile data: {str(e)}")
            # Fallback to ID token verification if available
            if 'id_token' in response:
                idinfo = id_token.verify_oauth2_token(
                    response['id_token'],
                    requests.Request(),
                    settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
                )
                
                extra_data = {
                    'email': idinfo['email'],
                    'name': idinfo.get('name', ''),
                    'picture': idinfo.get('picture', ''),
                    'given_name': idinfo.get('given_name', ''),
                    'family_name': idinfo.get('family_name', ''),
                }
                return self.get_provider().sociallogin_from_response(request, extra_data)
            raise


from rest_framework.response import Response
from rest_framework import status
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth import login
import requests
import jwt

class GoogleLogin(SocialLoginView):
    adapter_class = CustomGoogleOAuth2Adapter
    
    def post(self, request, *args, **kwargs):
        auth_code = request.data.get('code')
        
        if not auth_code:
            return Response(
                {'error': 'Authorization code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange auth code for tokens
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'code': auth_code,
                'client_id': settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id'],
                'client_secret': settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret'],
                'redirect_uri': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
            
            # Get tokens from Google
            response = requests.post(
                token_url,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code != 200:
                return Response({
                    'error': 'Token exchange failed',
                    'details': response.text
                }, status=status.HTTP_400_BAD_REQUEST)
            
            tokens = response.json()
            
            # Decode ID token to get email
            id_token = tokens.get('id_token')
            if not id_token:
                raise ValidationError("No ID token found")
            
            decoded_token = jwt.decode(id_token, options={"verify_signature": False})
            email = decoded_token.get('email')
            
            if not email:
                raise ValidationError("No email found in Google OAuth response")
            
            # Check if user exists
            User = get_user_model()
            existing_user = User.objects.filter(email=email).first()
            
            if existing_user:
                # Specify the backend explicitly
                from django.contrib.auth.backends import ModelBackend
                
                # Log in the user with the specified backend
                existing_user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, existing_user)
                
                # Generate tokens manually
                from rest_framework_simplejwt.tokens import RefreshToken
                refresh = RefreshToken.for_user(existing_user)
                
                return Response({
                    'refresh': str(refresh),
                    'access_token': str(refresh.access_token),
                    'user': {
                        'email': existing_user.email,
                        'username': existing_user.username,
                        # Add any other user fields you want to return
                    }
                })
            
            # Prepare request data for social login
            request.data['access_token'] = tokens.get('access_token')
            request.data['id_token'] = id_token
            
            # Call parent method to handle social login
            response = super().post(request, *args, **kwargs)
            
            return response
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)