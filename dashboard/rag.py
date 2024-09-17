import io
import sys
from functools import lru_cache
from typing import List, Optional
from pathlib import Path
import asyncio
import chromadb
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
        self.chroma_client, self.chroma_collection, self.vector_store, self.storage_context = self.initialize_client()
        self.embed_model = embed_model

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
    
    # def process_document(self, file_stream: io.BytesIO, file_key: str):
        

    #     documents = SimpleDirectoryReader(input_dir=None, input_files=file_stream).load_data()  # Assuming load_data has an async version
    #     splitter = SentenceSplitter(chunk_size=1024)
    #     nodes = splitter.get_nodes_from_documents(documents)

    #     # Generate embeddings for each node asynchronously
    #     # await asyncio.gather(*[
    #     #     self.embed_node(node) for node in nodes
    #     # ])

    #     # Create vector and summary indices
    #     vector_index = VectorStoreIndex(nodes, storage_context=self.storage_context)
    #     summary_index = SummaryIndex(nodes, storage_context=self.storage_context)

    #     return vector_index, summary_index
    async def process_document(self, user_id_filename,file_stream: io.BytesIO):
        # Write the bytes to a temporary file
        temp_file_name = f"{user_id_filename}.tmp"

        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp', prefix=user_id_filename) as temp_file:
            temp_file.write(file_stream.read())
            temp_file.flush()  # Ensure data is written to disk

        # Use the temporary file for loading data
        documents = SimpleDirectoryReader(input_dir=None, input_files=[temp_file.name]).load_data()
        
        splitter = SentenceSplitter(chunk_size=1024)
        nodes = splitter.get_nodes_from_documents(documents)

        # Generate embeddings for each node asynchronously
        # tasks = [self.embed_node(node) for node in nodes]
        # await asyncio.gather(*tasks)

        # Create vector and summary indices
        vector_index = VectorStoreIndex(nodes, storage_context=self.storage_context, embed_model=self.embed_model)
        summary_index = SummaryIndex(nodes, storage_context=self.storage_context, embed_model=self.embed_model)

        return vector_index, summary_index

    async def embed_node(self, node):
        node.text = self.clean_text(node.text)
        node.embedding = await self.embed_model.get_text_embedding(node.text)

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
    

    async def del_embeddings(self,user_id_filename) -> bool:
        try:

            # Deleting embeddings associated with the file_key
            self.chroma_collection.delete(where={"file_name": user_id_filename})
            return True
        except Exception as e:
            # Log the error or handle it as needed
            print(f"Error deleting embeddings for {user_id_filename}: {e}")
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
        # Create the VectorStoreIndex from the vector store
        index = VectorStoreIndex.from_vector_store(self.vector_store, embed_model=embed_model)
        
        # Create the query engine
        query_engine = index.as_query_engine(similarity_top_k=4)
        
        # Execute the query and return the response
        response = query_engine.query(query)
        return response
    

# class DocumentProcessor:
#     def __init__(self, user_id):
#         self.user_id = user_id
#         self.embed_model = embed_model
#         self.chroma_client, self.chroma_collection, self.vector_store, self.storage_context = self.initialize_client()

#     def initialize_client(self):
#         collection_name = f"user_{self.user_id}_collection"
#         chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
#         chroma_collection = chroma_client.get_or_create_collection(collection_name)
#         vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
#         storage_context = StorageContext.from_defaults(vector_store=vector_store)
#         return chroma_client, chroma_collection, vector_store, storage_context

#     async def is_document_indexed(self, file_key: str) -> bool:
#         check = await sync_to_async(self.chroma_collection.get)(where={"file_path": file_key})
#         # Ensure check is not a dictionary, and correctly handle the return type
#         if check and 'ids' in check:
#             return bool(check['ids'])
#         return False

#     async def process_document(self, file_stream: io.BytesIO, file_key: str):
        

#         documents = SimpleDirectoryReader(input_dir=None, input_files=file_stream).load_data()  # Assuming load_data has an async version
#         splitter = SentenceSplitter(chunk_size=1024)
#         nodes = splitter.get_nodes_from_documents(documents)

#         # Generate embeddings for each node asynchronously
#         await asyncio.gather(*[
#             self.embed_node(node) for node in nodes
#         ])

#         # Create vector and summary indices
#         vector_index = VectorStoreIndex(nodes, storage_context=self.storage_context)
#         summary_index = SummaryIndex(nodes, storage_context=self.storage_context)

#         return vector_index, summary_index

#     async def embed_node(self, node):
#         node.text = self.clean_text(node.text)
#         node.embedding = await self.embed_model.get_text_embedding_async(node.text)  # Assuming get_text_embedding has an async version

#     async def create_tools_from_stored_data(self, file_key):
#         nodes = await self.vector_store._get(limit=sys.maxsize, where={"file_path": file_key}).nodes
#         vector_index = VectorStoreIndex(nodes)
#         summary_index = SummaryIndex(nodes)

#         return await self.create_tools(vector_index, summary_index, name="from_stored_data")

#     async def create_tools(self, vector_index, summary_index, name: str):
#         async def vector_query(query: str, page_numbers: Optional[List[str]] = None) -> str:
#             page_numbers = page_numbers or []
#             metadata_dicts = [{"key": "page_label", "value": p} for p in page_numbers]
#             query_engine = vector_index.as_query_engine(similarity_top_k=2)
#             response = await query_engine.query_async(query)  # Assuming query has an async version
#             return response

#         async def summary_query(query: str) -> str:
#             summary_engine = summary_index.as_query_engine(response_mode="tree_summarize")
#             response = await summary_engine.query_async(query)  # Assuming query has an async version
#             return response

#         vector_tool = FunctionTool.from_defaults(name=f"vector_tool_{name}", fn=vector_query)
#         summary_tool = FunctionTool.from_defaults(fn=summary_query, name=f"summary_tool_{name}")
#         return vector_tool, summary_tool

#     def clean_text(self, text):
#         return text.strip()