
from dotenv import load_dotenv, find_dotenv
import os
import requests
import boto3
from botocore.client import Config
import mimetypes
from Kontra.settings import CDN_CUSTOM_DOMAIN_STATIC_IMG

def load_env():
    dotenv_path = find_dotenv(filename=".env")
    if dotenv_path:
        load_dotenv(dotenv_path)
        print(f"Loaded environment variables from {dotenv_path}")
    else:
        raise FileNotFoundError("Could not find the .env file.")

def get_openai_api_key():
    load_env()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("OPENAI_API_KEY not found in the environment file.")
    return openai_api_key






# Configuration for Cloudflare R2
CLOUDFLARE_R2_ENDPOINT = 'https://7abf97ac04a5eb2b6809e464d5b6d65d.r2.cloudflarestorage.com'
BUCKET_NAME = 'static'
AWS_ACCESS_KEY_ID = '63bb2bd1e7b7d4edb9323f2c5fcb1b90'
AWS_SECRET_ACCESS_KEY = '5761bb40b1a82d893ee5bb99f58d5cb3e29af644e1c78d1d7c9dd84ca71c4cc1'

# Initialize Cloudflare session
cloudflare_session = boto3.session.Session()
cloudflare_client = cloudflare_session.client(
    "s3",
    region_name="auto",
    endpoint_url=CLOUDFLARE_R2_ENDPOINT,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4")
)

def upload_document(file_key, file):
    """
    Uploads a document to Cloudflare R2 and constructs a permanent public URL for access.
    
    Args:
        file_key (str): The destination file key (path) in the Cloudflare R2 bucket.
        file (file-like object): The file object to upload (opened in binary mode).
    
    Returns:
        tuple: A tuple with (True, permanent_url) on success or (False, error_message) on failure.
    """
    try:
        
        # Determine the MIME type of the file
        mime_type, _ = mimetypes.guess_type(file_key)
        file_extension = file_key.split('.')[-1].lower()

        # Fallback MIME type for unsupported or ambiguous file types
        if not mime_type:
            if file_extension == 'pdf':
                mime_type = 'application/pdf'
            elif file_extension in ['doc', 'docx']:
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_extension == 'txt':
                mime_type = 'text/plain'
            elif file_extension in ['png', 'jpg', 'jpeg', 'gif']:
                mime_type = f'image/{file_extension}'
            else:
                return False, f"Unsupported file type: {file_extension}"

        # Check if the file is empty
        file.seek(0, 2)  # Move the pointer to the end of the file to get the size
        file_size = file.tell()
        file.seek(0)  # Reset file pointer to the beginning

        if file_size == 0:
            return False, "The submitted file is empty."

        # Upload file to Cloudflare R2
        response= cloudflare_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_key,
            Body=file,
            ContentType=mime_type
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            # Construct the permanent public URL
            permanent_url = f"{CDN_CUSTOM_DOMAIN_STATIC_IMG}{file_key}"

            print(f"File {file_key} uploaded successfully. Permanent URL: {permanent_url}")
            return True, permanent_url
        else:
            error_message = f"Upload failed. Status code: {response['ResponseMetadata']['HTTPStatusCode']}"
            print(error_message)
            return False, error_message

    except Exception as e:
        print(f"Exception during file upload: {e}")
        return False, str(e)