
from celery import shared_task
from .models import Document
from .rag import DocumentProcessor
import io
import requests
import os


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self,file_key, user_id, document_id, cloudflare_url):
    
    try:
        response = requests.get(cloudflare_url)
        if response.status_code == 200:
            file_content = response.content
        else:
            print(f"Error: Failed to download file from Cloudflare: {response.status_code}")
            return

        user_id_filename = f"{user_id}_{file_key}"
        base_filename = os.path.splitext(user_id_filename)[0]
        doc_processor = DocumentProcessor(user_id)
        # Ensure this is a synchronous call
        vector_index, summary_index = doc_processor.process_document(base_filename, io.BytesIO(file_content))

        document = Document.objects.get(pk=document_id)
        if vector_index and summary_index:
            document.embeddings_stored = True
            document.file_key = base_filename
            document.save()
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        self.retry(exc=e)

@shared_task
def delete_embeddings_task(file_key,user_id):
    try:
    
        doc_processor = DocumentProcessor(user_id=user_id)
        success = doc_processor.del_embeddings(file_key)
        if success:
            print(f"Successfully deleted embeddings for {file_key}")
        else:
            print(f"Failed to delete embeddings for {file_key}")
    except Exception as e:
        print(f"Error deleting embeddings: {str(e)}")
