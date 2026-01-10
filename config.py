import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Config:
    # Tree-sitter configurations
    TREE_SITTER_LANGUAGES = ['java', 'kotlin']
    PARSING_CHUNK_SIZE = 1000  # Lines of code per chunk
    
    # Embedding configurations
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    MAX_SEQUENCE_LENGTH = 256
    
    # ChromaDB configurations
    CHROMA_PERSIST_DIR = "./chroma_db"
    COLLECTION_NAME = "android_code_embeddings"
    
    # File patterns for Android projects
    SOURCE_FILE_PATTERNS = ['*.java', '*.kt', '*.xml']
    
    # Pipeline configurations
    BATCH_SIZE = 32
    METADATA_FIELDS = ['file_path', 'language', 'node_type', 'function_name', 'class_name']
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not os.path.exists(cls.CHROMA_PERSIST_DIR):
            os.makedirs(cls.CHROMA_PERSIST_DIR, exist_ok=True)