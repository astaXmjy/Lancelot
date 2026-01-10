# Embeddings module
import torch
from transformers import AutoTokenizer, AutoModel
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class CodeEmbeddingsGenerator:
    def __init__(self, model_name: str = None):
        """Initialize the embedding model"""
        config = __import__('config').Config
        self.model_name = model_name or config.EMBEDDING_MODEL
        
        try:
            # Use sentence-transformers for better semantic embeddings
            self.model = SentenceTransformer(self.model_name)
            self.tokenizer = None  # Not needed with sentence-transformers
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            logger.info(f"Loaded embedding model {self.model_name} on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        try:
            with torch.no_grad():
                embedding = self.model.encode(
                    text,
                    convert_to_tensor=True,
                    show_progress_bar=False
                )
                if self.device == 'cuda':
                    embedding = embedding.cpu()
                return embedding.numpy()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings in batch for efficiency"""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                convert_to_tensor=True,
                show_progress_bar=True
            )
            
            if self.device == 'cuda':
                embeddings = embeddings.cpu()
            
            return [emb.numpy() for emb in embeddings]
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {e}")
            return [np.zeros(self.model.get_sentence_embedding_dimension()) 
                   for _ in range(len(texts))]
    
    def prepare_text_for_embedding(self, code_chunk: Dict) -> str:
        """Prepare code chunk text for embedding"""
        # Extract relevant information
        text_parts = []
        
        if 'name' in code_chunk:
            text_parts.append(f"Name: {code_chunk['name']}")
        
        if 'node_type' in code_chunk:
            text_parts.append(f"Type: {code_chunk['node_type']}")
        
        if 'text' in code_chunk:
            # Truncate code if too long
            code_text = code_chunk['text']
            if len(code_text) > 1000:
                code_text = code_text[:500] + " ... " + code_text[-500:]
            text_parts.append(f"Code:\n{code_text}")
        
        if 'relative_path' in code_chunk:
            text_parts.append(f"File: {code_chunk['relative_path']}")
        
        return "\n\n".join(text_parts)