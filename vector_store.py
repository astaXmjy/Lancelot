# Vector store module
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
import logging
from config import Config

logger = logging.getLogger(__name__)

class ChromaVectorStore:
    def __init__(self, collection_name: str = None):
        """Initialize ChromaDB client and collection"""
        self.config = Config
        self.collection_name = collection_name or self.config.COLLECTION_NAME
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.config.CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )
            logger.info(f"Created new collection: {self.collection_name}")
    
    def store_embeddings(self, 
                        embeddings: List[List[float]],
                        documents: List[str],
                        metadatas: List[Dict[str, Any]],
                        ids: Optional[List[str]] = None) -> bool:
        """Store embeddings in ChromaDB"""
        try:
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(documents))]
            
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Stored {len(documents)} embeddings in ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
            return False
    
    def search_similar(self, 
                      query_embedding: List[float],
                      n_results: int = 5,
                      where_filter: Optional[Dict] = None) -> Dict:
        """Search for similar code chunks"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=['documents', 'metadatas', 'distances']
            )
            return results
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {e}")
            return {}
    
    def delete_collection(self):
        """Delete the current collection"""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_embeddings": count,
                "persist_directory": self.config.CHROMA_PERSIST_DIR
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}