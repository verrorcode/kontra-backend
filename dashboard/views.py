# views.py

from django.http import JsonResponse
from django.views import View
from django.core.files.base import ContentFile
import io
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


# Work in Progress
@method_decorator(csrf_exempt, name='dispatch')
class RechargeCredits(LoginRequiredMixin, View):
    pass
@method_decorator(csrf_exempt, name='dispatch')
class UpgradePlanView(LoginRequiredMixin, TemplateView):
    template_name = 'upgrade_plan.html'
    pass
@method_decorator(csrf_exempt, name='dispatch')
class RechargeCreditsView(LoginRequiredMixin, View):
    pass





# Done 

class ChatDashboardView(LoginRequiredMixin, View):
    template_name = 'chat_dashboard.html'

    def get(self, request, *args, **kwargs):
        # Fetch all chat messages for the logged-in user, ordered by timestamp
        messages = ChatMessage.objects.filter(user=request.user).order_by('timestamp')
        
        # Fetch the user's profile
        user_profile = get_object_or_404(UserProfile, user=request.user)
        
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

@method_decorator(csrf_exempt, name='dispatch')
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

@method_decorator(csrf_exempt, name='dispatch')
class UserProfileView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        user_profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

@method_decorator(csrf_exempt, name='dispatch')
class DocumentUploadView(View):
    async def post(self, request, *args, **kwargs):
        user = request.user  # Get the user
        user_profile = UserProfile.objects.get(user=user)
        saas_plan = user_profile.saas_plan
        total_docs = user_profile.total_documents_uploaded
        total_storage_used = user_profile.total_storage_used
        response_data = []

        if not user_profile.is_plan_active:
            return JsonResponse({"status": "error", "message": "Your plan is not active"})

        # Iterate over all uploaded files
        for file in request.FILES.getlist('document'):
            file_key = file.name
            file_size = file.size / (1024 * 1024)  # Convert file size to MB

            # Check if the total storage exceeds the plan's limit
            if total_storage_used + file_size > user_profile.saas_plan.max_storage_mb:
                response_data.append({"status": "error", "file": file_key, "message": "Storage limit exceeded"})
                continue  # Skip to the next file
            
            # Check if the total documents exceed the plan's limit
            if total_docs >= saas_plan.max_documents:
                response_data.append({"status": "error", "file": file_key, "message": "Documents limit exceeded"})
                continue  # Skip to the next file

            # Upload the document to Cloudflare asynchronously
            try:
                cloud_url = await upload_document(file_key, file)  # Await the async file upload function
            except Exception as e:
                response_data.append({"status": "error", "file": file_key, "message": f"Failed to upload to Cloudflare: {str(e)}"})
                continue  # Skip to the next file if upload fails

            # Initialize the DocumentProcessor for the specific user
            doc_processor = DocumentProcessor(user.id)

            # Process the document directly from the uploaded file
            file_stream = io.BytesIO(file.read())
             
            if doc_processor.process_document_embeddings(file_stream, file_key):
                # Save the document and its metadata to the database
                Document.objects.create(
                    user=user,
                    file=file,
                    file_type=file.content_type,
                    embedding= True ,  # You can update this later if needed
                    folder=request.data.get("folder_id"),  # Set a folder if required
                    file_size=file_size,  # Save the file size in MB
                    cloudflare_url=cloud_url  # Save the uploaded file's Cloudflare URL
                )
                response_data.append({"status": "success", "file": file_key, "message": "Document processed"})
                
            else:
                response_data.append({"status": "error", "file": file_key, "message": "Failed to process document"})

        return JsonResponse(response_data, safe=False)


@method_decorator(csrf_exempt, name='dispatch')
class  OpenFolderView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        folder = request.data.get('folder_id')
        docs = Document.objects.get(folder_id = folder)
        return docs
    
@method_decorator(csrf_exempt, name='dispatch')
class CreateFolderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        folder_name = request.data.get('folder_name')
        Folder.objects.create(user=request.user, name=folder_name)
        return redirect('settings')

@method_decorator(csrf_exempt, name='dispatch')
class DeleteDocumentView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # Get the document belonging to the authenticated user
        document = get_object_or_404(Document, id=kwargs['document_id'], user=request.user)

        # Extract the file key (assuming the document name is stored in the file field)
        file_key = document.file.name

        # Create an instance of DocumentProcessor with the user ID
        doc_processor = DocumentProcessor(request.user.id)

        # Call the asynchronous delete embeddings function using async_to_sync
        async_to_sync(doc_processor.del_embeddings)(file_key)

        # Delete the document from the database
        document.delete()

        # Redirect to the settings page after successful deletion
        return redirect('settings')

@method_decorator(csrf_exempt, name='dispatch')
class DeleteFolderView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        folder = get_object_or_404(Folder, id=kwargs['folder_id'], user=request.user)
        
        # Get all documents associated with this folder
        documents = Document.objects.filter(folder=folder)
        
        if documents.exists():
            # Initialize the DocumentProcessor for the current user
            doc_processor = DocumentProcessor(request.user.id)

            # Create an async task list to delete embeddings for all documents in the folder
            tasks = []
            for document in documents:
                file_key = document.file.name  # Assuming file_key is the file name
                tasks.append(doc_processor.del_embeddings(file_key))

            # Run all the delete tasks asynchronously
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.gather(*tasks))  # Directly run async tasks
            
            # Delete all the documents after embeddings have been removed
            documents.delete()

        # Delete the folder itself
        folder.delete()

        return redirect('settings')




