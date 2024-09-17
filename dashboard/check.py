
# this the the documenl upload api to be tested as this doesn not involve creating temporary directory in the server.
import io
from django.http import JsonResponse
from django.views import View
from django.db import transaction
from .models import UserProfile, Document
from .document_processor import DocumentProcessor
from .file_uploader import upload_document  # Async upload function

class DocumentUploadView(View):
    async def post(self, request, *args, **kwargs):
        user = request.user
        user_profile = await self.get_user_profile(user)
        saas_plan = user_profile.saas_plan
        response_data = []

        if not user_profile.is_plan_active:
            return JsonResponse({"status": "error", "message": "Your plan is not active"})

        for file in request.FILES.getlist('document'):
            file_key = file.name
            file_size_mb = file.size / (1024 * 1024)  # Convert file size to MB

            if await self.is_storage_limit_exceeded(user, file_size_mb, saas_plan):
                response_data.append({"status": "error", "file": file_key, "message": "Storage limit exceeded"})
                continue

            if await self.is_documents_limit_exceeded(user, saas_plan):
                response_data.append({"status": "error", "file": file_key, "message": "Documents limit exceeded"})
                continue

            try:
                cloud_url = await upload_document(file_key, file)  # Await async upload
                success = await self.process_and_save_document(user, file, file_key, file_size_mb, request.POST.get("folder_id"))
                
                if success:
                    response_data.append({"status": "success", "file": file_key, "message": "Document processed and uploaded"})
                else:
                    response_data.append({"status": "error", "file": file_key, "message": "Failed to process document"})
            except Exception as e:
                response_data.append({"status": "error", "file": file_key, "message": f"Error: {str(e)}"})

        return JsonResponse(response_data, safe=False)

    async def get_user_profile(self, user):
        return await UserProfile.objects.select_related('saas_plan').aget(user=user)

    async def is_storage_limit_exceeded(self, user, file_size_mb, saas_plan):
        total_storage_used = await self.get_total_storage_used(user)
        return total_storage_used + file_size_mb > saas_plan.max_storage_mb

    async def is_documents_limit_exceeded(self, user, saas_plan):
        total_docs = await self.get_total_documents(user)
        return total_docs >= saas_plan.max_documents

    async def process_and_save_document(self, user, file, file_key, file_size, folder_id):
        file_stream = io.BytesIO(file.read())
        doc_processor = DocumentProcessor(user.id)

        if doc_processor.process_document_embeddings(file_stream, file_key):
            await self.save_document(user, file, file_key, file_size, folder_id)
            await self.update_user_profile(user)
            return True
        return False

    @transaction.atomic
    async def save_document(self, user, file, file_key, file_size, folder_id):
        await Document.objects.create(
            user=user,
            file=file_key,  # Save the file_key instead of the file object
            file_type=file.content_type,
            folder_id=folder_id,
            file_size=file_size
        )

    @transaction.atomic
    async def update_user_profile(self, user):
        user_profile = await UserProfile.objects.get(user=user)
        user_profile.total_documents_uploaded = await Document.objects.filter(user=user).count()
        user_profile.update_total_storage_used()
        await user_profile.save()