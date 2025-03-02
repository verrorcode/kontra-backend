import io
import sys
from functools import lru_cache
from typing import List, Optional
from pathlib import Path
import os
import chromadb
import uuid
from asgiref.sync import sync_to_async
from llama_index.core import VectorStoreIndex, SummaryIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from transformers import AutoModelForCausalLM, AutoTokenizer
from llama_index.core.tools import FunctionTool
from .variables import CHROMA_DB_PATH, llm, embed_model
from llama_index.core.vector_stores import MetadataFilters, FilterCondition
import tempfile
import nest_asyncio
nest_asyncio.apply()
Settings.llm = llm
Settings.embed_model = embed_model

class DocumentProcessor:
    def __init__(self, user_id):
        self.user_id = user_id
        self.embed_model = embed_model
        self.chroma_client, self.chroma_collection, self.vector_store, self.storage_context = self.initialize_client()
        

    def initialize_client(self):
        collection_name = f"user_{self.user_id}_collection"
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return chroma_client, chroma_collection, vector_store, storage_context


    def is_document_indexed(self, file_key: str) -> bool:
        check = self.chroma_collection.get(where={"file_path": file_key})
        return bool(check and check['ids'])

    def process_document_stream(self, file_stream: io.BytesIO, file_key: str):
        if self.is_document_indexed(file_key):
            return self.create_tools_from_stored_data(file_key)

        documents = SimpleDirectoryReader(input_dir=None, input_stream=file_stream).load_data()
        splitter = SentenceSplitter(chunk_size=1024)
        nodes = splitter.get_nodes_from_documents(documents)

        # Generate embeddings for each node
        for node in nodes:
            node.text = self.clean_text(node.text)
            node.embedding = embed_model.get_text_embedding(node.text)

        # Create vector and summary indices
        vector_index = VectorStoreIndex(nodes, storage_context=self.storage_context)
        summary_index = SummaryIndex(nodes, storage_context=self.storage_context)

        # Persist the vector store and summary index
        # vector_index.storage_context.vector_store.persist(persist_path=f"./chroma_db/user_{self.user_id}")
        # summary_index.storage_context.vector_store.persist(persist_path=f"./chroma_db/user_{self.user_id}")

        return vector_index, summary_index
    
    def process_document(self, base_filename, file_stream: io.BytesIO):
        # Set up the temporary file path with the exact base file name
        temp_file_name = os.path.join(tempfile.gettempdir(), base_filename)
        # temp_file_name = os.path.join(tempfile.gettempdir(), f"{base_filename}_{uuid.uuid4()}")

        try:
            # Write the bytes to the file with the exact name
            with open(temp_file_name, 'wb') as temp_file:
                temp_file.write(file_stream.read())
                print(temp_file_name)  # Ensure correct file name
                temp_file.flush()

            # Use the temporary file for loading data
            documents = SimpleDirectoryReader(input_dir=None, input_files=[temp_file_name]).load_data()

            splitter = SentenceSplitter(chunk_size=1024)
            nodes = splitter.get_nodes_from_documents(documents)

            # Create vector and summary indices
            vector_index = VectorStoreIndex(nodes, storage_context=self.storage_context, embed_model=self.embed_model)
            summary_index = SummaryIndex(nodes, storage_context=self.storage_context, embed_model=self.embed_model)

            return vector_index, summary_index

        finally:
            # Ensure that the temporary file is deleted
            if os.path.exists(temp_file_name):
                os.remove(temp_file_name)


    def embed_node(self, node):
        node.text = self.clean_text(node.text)
        node.embedding = self.embed_model.get_text_embedding(node.text)

    def clean_text(self, text):
        return text.strip()
    
    def create_tools_from_stored_data(self, file_key):
        nodes = self.vector_store._get(limit=sys.maxsize, where={"file_path": file_key}).nodes
        vector_index = VectorStoreIndex(nodes)
        summary_index = SummaryIndex(nodes)

        vector_tool, summary_tool = self.create_tools(vector_index, summary_index, name="from_stored_data")
        return vector_tool, summary_tool
    
    def create_tools(self, vector_index, summary_index, name: str):
        def vector_query(query: str, page_numbers: Optional[List[str]] = None) -> str:
            page_numbers = page_numbers or []
            metadata_dicts = [{"key": "page_label", "value": p} for p in page_numbers]
            query_engine = vector_index.as_query_engine(
                similarity_top_k=2,
                filters=MetadataFilters.from_dicts(
                    metadata_dicts, condition=FilterCondition.OR
                ),
            )
            response = query_engine.query(query)
            return response

        def summary_query(query: str) -> str:
            summary_engine = summary_index.as_query_engine(response_mode="tree_summarize", use_async=True)
            response = summary_engine.query(query)
            return response

        vector_tool = FunctionTool.from_defaults(name=f"vector_tool_{name}", fn=vector_query)
        summary_tool = FunctionTool.from_defaults(fn=summary_query, name=f"summary_tool_{name}")
        return vector_tool, summary_tool

    def clean_text(self, text):
        return text.strip()
    

    def del_embeddings(self, file_key, batch_size=5461) -> bool:
        try:
            # Check if embeddings exist for the file_key before deletion
            embeddings = self.chroma_collection.get(where={"file_name": file_key})
            
            if not embeddings["ids"]:
                print(f"No embeddings found for {file_key}")
                return False
            
            # Get the list of IDs to delete
            embedding_ids = embeddings["ids"]
            total_embeddings = len(embedding_ids)
            
            # Process deletion in batches
            for i in range(0, total_embeddings, batch_size):
                batch_ids = embedding_ids[i:i + batch_size]
                self.chroma_collection.delete(ids= list(batch_ids),where={"file_name": file_key})
                print(f"Deleted {len(batch_ids)} embeddings for {file_key}")
            
            print(f"Successfully deleted all embeddings for {file_key}")
            return True
        
        except Exception as e:
            # Log the error or handle it as needed
            print(f"Error deleting embeddings for {file_key}: {e}")
            return False
         
class Querying:
    def __init__(self, user_id):
        self.user_id = user_id
        self.vector_store = self.initialize_client()

    def initialize_client(self):
        collection_name = f"user_{self.user_id}_collection"
        chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        chroma_collection = chroma_client.get_or_create_collection(collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        return vector_store
    
    def query(self, query: str):
        
        from .variables import llm, embed_model
        try:
            # Create the VectorStoreIndex from the vector store
            index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
            
            # Create the query engine
            query_engine = index.as_query_engine(similarity_top_k=4)
            
            # Execute the query
            response = query_engine.query(query)
            print(response)
            # Log and return the response
            
            return response
        except Exception as e:
            
            return "An error occurred while processing your query. Please create a ticket"

