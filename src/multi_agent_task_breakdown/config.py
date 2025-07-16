"""
Core configuration for Multi-Agent Task Breakdown system.
Sets up AWS Bedrock LLM, embeddings, and memory systems.
"""

import os
from typing import Optional

from langchain_aws import BedrockLLM
from langchain_community.embeddings import BedrockEmbeddings
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for the multi-agent system."""
    
    def __init__(
        self,
        model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
        embedding_model_id: str = "amazon.titan-embed-text-v1",
        region_name: str = "us-east-1",
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ):
        self.model_id = model_id
        self.embedding_model_id = embedding_model_id
        self.region_name = region_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize LLM and embeddings
        self.llm = self._setup_llm()
        self.embeddings = self._setup_embeddings()
        
        # Initialize memory systems
        self.short_term_memory = self._setup_short_term_memory()
        self.vector_store = self._setup_vector_store()
        self.long_term_memory = self._setup_long_term_memory()
    
    def _setup_llm(self) -> BedrockLLM:
        """Setup AWS Bedrock LLM."""
        return BedrockLLM(
            model_id=self.model_id,
            region_name=self.region_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            model_kwargs={
                "anthropic_version": "bedrock-2023-05-31"
            }
        )
    
    def _setup_embeddings(self) -> BedrockEmbeddings:
        """Setup AWS Bedrock embeddings."""
        return BedrockEmbeddings(
            model_id=self.embedding_model_id,
            region_name=self.region_name
        )
    
    def _setup_short_term_memory(self) -> ConversationBufferMemory:
        """Setup short-term conversation memory."""
        return ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def _setup_vector_store(self) -> FAISS:
        """Setup FAISS vector store for long-term memory."""
        # Initialize with empty texts to create the store
        return FAISS.from_texts([""], self.embeddings)
    
    def _setup_long_term_memory(self) -> VectorStoreRetrieverMemory:
        """Setup long-term memory with vector store retrieval."""
        return VectorStoreRetrieverMemory(
            retriever=self.vector_store.as_retriever(search_kwargs={"k": 5}),
            memory_key="relevant_context"
        )


# Global configuration instance
config = Config()