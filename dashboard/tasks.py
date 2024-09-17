from background_task import background
from .models import Document
from .rag import DocumentProcessor
import io
import os
import requests
import asyncio


@background(schedule=0)
def process_document_task(file_key,user_id, document_id, cloudflare_url):
    try:
        print(cloudflare_url)
        # import pdb;pdb.set_trace()
        # Fetch the file from the Cloudflare URL
        response = requests.get(cloudflare_url)
        if response.status_code == 200:
            file_content = response.content  # This is bytes
        else:
            print(f"Error: Failed to download file from Cloudflare: {response.status_code}")
            return
        user_id_filename = str(user_id) + '_' + file_key
        # Initialize the document processor
        doc_processor = DocumentProcessor(user_id)
        
        # Call the async process_document function properly
        vector_index, summary_index = asyncio.run(doc_processor.process_document(user_id_filename,io.BytesIO(file_content)))
        
        # Fetch and update the document
        document = Document.objects.get(pk=document_id)
        if vector_index and summary_index:
            document.embeddings_stored = True
            document.save()

    except Exception as e:
        # Handle exceptions
        print(f"Error processing document: {str(e)}")


@background(schedule=0)
def delete_embeddings_task(file_key, user_id):
    try:
        user_id_filename = str(user_id) + '_' + file_key
        # Initialize the document processor with a relevant user_id or context
        doc_processor = DocumentProcessor(user_id=user_id)
        success = asyncio.run(doc_processor.del_embeddings(user_id_filename))
        if success:
            print(f"Successfully deleted embeddings for {file_key}")
        else:
            print(f"Failed to delete embeddings for {file_key}")
    except Exception as e:
        print(f"Error deleting embeddings: {str(e)}")