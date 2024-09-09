
from dotenv import load_dotenv, find_dotenv
import requests
import httpx
import os
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





async def upload_document(file_key, file, token='4dMi7i49'):
    url = 'https://api.admirian.com/commons/upload/static/'
    headers = {
        'TOKEN': token
    }

    # Determine the MIME type based on file extension
    file_extension = file_key.split('.')[-1].lower()
    if file_extension in ['pdf']:
        mime_type = 'application/pdf'
    elif file_extension in ['doc', 'docx']:
        mime_type = 'application/msword'  # for older doc format, application/vnd.openxmlformats-officedocument.wordprocessingml.document for docx
    elif file_extension in ['txt']:
        mime_type = 'text/plain'
    else:
        raise ValueError("Unsupported file type. Only PDF, DOC, DOCX, and TXT files are allowed.")

    files = {
        'type': (None, 'static'),
        'mime_type': (None, mime_type),
        'file': (file_key, file.read(), mime_type)
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, files=files)

    if response.status_code == 200:
        response_json = response.json()
        if 'url' in response_json:
            return response_json['url']
        else:
            raise ValueError("The response did not contain a 'url' field.")
    else:
        response.raise_for_status()
