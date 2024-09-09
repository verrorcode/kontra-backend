from llama_index.core import StorageContext
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from variables import CHROMA_DB_PATH
def initialize_client(user_id):
    collection_name = f"user_{user_id}_collection"
    chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH) # put this into variables.py
    chroma_collection = chroma_client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return chroma_collection, vector_store, storage_context


