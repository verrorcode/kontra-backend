# views.py
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View

class CustomEmailVerificationView(View):
    def get(self, request, key):
        # This view does not verify the email; it simply returns a response or redirects
        # Redirect to your FlutterFlow page or desired URL
        return redirect(f'http://localhost:8000/api/auth/registration/verify-email?key={key}')
