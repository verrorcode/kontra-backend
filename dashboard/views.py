# views.py

from django.http import JsonResponse
from django.views import View
from django.core.files.base import ContentFile
import numpy as np
import os
from django.contrib.auth.decorators import login_required
from pathlib import Path
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, ListView
from django.views.decorators.csrf import csrf_exempt
from .models import Folder, Document, ChatMessage, UserProfile
from channels.db import database_sync_to_async
from .utils import get_openai_api_key, upload_document
import pdb
from asgiref.sync import async_to_sync
from .variables import SaasPlanDocuments
from .rag import DocumentProcessor
import asyncio
from .serializer import UserProfileSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from asgiref.sync import sync_to_async
from django.db import transaction
from django.db.models import Sum
import tempfile
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
from .tasks import process_document_task, delete_embeddings_task  # Import the background task
from decimal import Decimal
# Work in Progress

class RechargeCredits(LoginRequiredMixin, View):
    pass

class UpgradePlanView(LoginRequiredMixin, TemplateView):
    template_name = 'upgrade_plan.html'
    pass

class RechargeCreditsView(LoginRequiredMixin, View):
    pass





# Done 

class DocumentUploadView(View):
    def post(self, request, *args, **kwargs):
        user = request.user
        response_data = self.process_documents(user, request.FILES, request.POST)
        return JsonResponse(response_data, safe=False)

    def process_documents(self, user, files, post_data):
        response_data = []
        user_profile = self.get_user_profile(user)
        saas_plan = user_profile.saas_plan

        if not user_profile.is_plan_active:
            return [{"status": "error", "message": "Your plan is not active"}]

        for file in files.getlist('document'):
            file_key = file.name
            file_size = Decimal(file.size / (1024 * 1024))  # Convert file size to MB

            total_storage_used = Decimal(self.get_total_storage_used(user))

            max_storage_mb = Decimal(saas_plan.max_storage_mb)
            if total_storage_used + file_size > max_storage_mb:
                response_data.append({"status": "error", "file": file_key, "message": "Storage limit exceeded"})
                continue

            total_docs = self.get_total_documents(user)
            if total_docs >= saas_plan.max_documents:
                response_data.append({"status": "error", "file": file_key, "message": "Documents limit exceeded"})
                continue

            try:
                # Save document temporarily and process in the background
                temp_file_path = self.save_temp_file(file)
                document = self.save_document(user, file,  file_size, post_data.get("folder_id"))


                # Update document with cloudflare link after successful upload
                with open(temp_file_path, 'rb') as temp_file:
                    upload_success, cloudflare_link = upload_document(file_key, temp_file)
                
                if upload_success:
                    # Enqueue the document processing task
                    
                    process_document_task.delay(file_key, user.id, document.id, cloudflare_link)
                    document.cloudflare_link = cloudflare_link
                    document.save()
                    response_data.append({"status": "success", "file": file_key, "message": "Document uploaded and processing in background"})
                else:
                    response_data.append({"status": "error", "file": file_key, "message": "Failed to upload document"})
            except Exception as e:
                response_data.append({"status": "error", "file": file_key, "message": f"Error processing document: {str(e)}"})
            finally:
                os.unlink(temp_file_path)

        return response_data

    def save_temp_file(self, file):
        temp_file_path = tempfile.mktemp()  # Create a temporary file
        with open(temp_file_path, 'wb') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
        return temp_file_path
    
    def get_user_profile(self, user):
        return UserProfile.objects.select_related('saas_plan').get(user=user)

    def get_total_storage_used(self, user):
        return user.userprofile.total_storage_used

    def get_total_documents(self, user):
        return user.userprofile.total_documents_uploaded

    @transaction.atomic
    def save_document(self, user, file, file_size, folder_id):
        return Document.objects.create(
            user=user,
            file=file,
            file_type=file.content_type,
            folder_id=folder_id,
            file_size=file_size
        )


class DeleteFolderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(Folder, id=kwargs['folder_id'], user=request.user)
        
        # Get all documents associated with this folder
        documents = Document.objects.filter(folder=folder)
        
        if documents.exists():
            # Create async tasks to delete embeddings for all documents in the folder
            for document in documents:
                file_key = document.file_key
                # Use Celery's delay method to call the task asynchronously
                delete_embeddings_task.delay(file_key, request.user.id)

            # Delete all the documents after embeddings have been removed
            documents.delete()

        # Delete the folder itself
        folder.delete()
        profile = UserProfile.objects.get(user=request.user)
        profile.total_documents_uploaded = Document.objects.filter(user=request.user).count()
        profile.save()
        return redirect('settings')

class ChatDashboardView(LoginRequiredMixin, View):
    template_name = 'chat_dashboard.html'

    def get(self, request, *args, **kwargs):
        # Fetch or create the user's profile
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)

        # Fetch all chat messages for the logged-in user, ordered by timestamp
        messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')

        # Extract plan, status, and credits information
        plan = user_profile.saas_plan
        status = user_profile.is_plan_active
        credits = user_profile.credits + user_profile.recharged_credits

        # Prepare the context with messages and user profile details
        context = {
            'messages': messages,
            'plan': plan,
            'is_plan_active': status,
            'credits': credits,
        }

        # Render the template with the context
        return render(request, self.template_name, context)

class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all folders for the current user
        folders = Folder.objects.filter(user=self.request.user)
        
        # Prepare a dictionary to hold folders and their corresponding documents
        folders_with_documents = {}
        
        for folder in folders:
            # Fetch documents in each folder
            documents_in_folder = Document.objects.filter(user=self.request.user, folder=folder)
            folders_with_documents[folder] = documents_in_folder
        
        # Fetch documents that are not in any folder (in the base directory)
        base_directory_documents = Document.objects.filter(user=self.request.user, folder__isnull=True)
        
        # Add to context
        context['folders_with_documents'] = folders_with_documents
        context['base_directory_documents'] = base_directory_documents
        
        return context


class UserProfileView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)



class  OpenFolderView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        folder = request.data.get('folder_id')
        docs = Document.objects.get(folder_id = folder)
        return docs
    

class CreateFolderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        folder_name = request.POST.get('folder_name')
        Folder.objects.create(user=request.user, name=folder_name)
        return redirect('settings')


class DeleteDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Get the document belonging to the authenticated user
        document = get_object_or_404(Document, id=kwargs['document_id'], user=request.user)

        # Extract the file key (assuming the document name is stored in the file_key field)
        file_key = document.file_key

        # Create an instance of DocumentProcessor with the user ID
        # Call the Celery task to delete embeddings asynchronously
        delete_embeddings_task.delay(file_key, request.user.id)
        document.delete()
        # Optionally: delete the file from storage
        # document.file.delete(save=False)
        profile = UserProfile.objects.get(user=request.user)
        profile.total_documents_uploaded = Document.objects.filter(user=request.user).count()
        profile.save()  # This will trigger recalculating any related fields (like storage used) via the UserProfile mode

        # Redirect to the settings page after successful deletion
        return redirect('settings')