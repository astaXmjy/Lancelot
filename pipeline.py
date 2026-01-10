# Pipeline module
import argparse
import logging
from pathlib import Path
from typing import Optional
from langgraph_workflow import AndroidCodePipeline
from vector_store import ChromaVectorStore
from embeddings import CodeEmbeddingsGenerator
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AndroidCodeAnalysisPipeline:
    def __init__(self):
        self.pipeline = AndroidCodePipeline()
        self.vector_store = ChromaVectorStore()
        self.embedding_gen = CodeEmbeddingsGenerator()
    
    def process_project(self, project_path: str) -> dict:
        """Process complete Android project"""
        logger.info(f"Starting processing for project: {project_path}")
        
        # Run the LangGraph workflow
        result = self.pipeline.run(project_path)
        
        # Generate summary report
        report = {
            "project": project_path,
            "parsed_chunks": len(result.get('parsed_chunks', [])),
            "embeddings_generated": len(result.get('embeddings', [])),
            "storage_success": result.get('storage_success', False),
            "collection_stats": result.get('collection_stats', {})
        }
        
        logger.info(f"Processing completed: {json.dumps(report, indent=2)}")
        return report
    
    def search_similar_code(self, query: str, n_results: int = 5, 
                           filters: Optional[dict] = None) -> dict:
        """Search for similar code in the vector store"""
        logger.info(f"Searching for: {query}")
        
        # Generate embedding for query
        query_embedding = self.embedding_gen.generate_embedding(query).tolist()
        
        # Search in vector store
        results = self.vector_store.search_similar(
            query_embedding=query_embedding,
            n_results=n_results,
            where_filter=filters
        )
        
        return results
    
    def interactive_search(self):
        """Interactive search interface"""
        print("\n" + "="*50)
        print("Android Code Similarity Search")
        print("="*50)
        
        while True:
            print("\nOptions:")
            print("1. Search for similar code")
            print("2. Filter by language")
            print("3. Filter by file type")
            print("4. Show collection stats")
            print("5. Exit")
            
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == '1':
                query = input("Enter code or description to search: ").strip()
                if query:
                    results = self.search_similar_code(query)
                    self._display_results(results)
            
            elif choice == '2':
                language = input("Enter language (java/kotlin/xml): ").strip().lower()
                if language in ['java', 'kotlin', 'xml']:
                    filters = {"language": language}
                    query = input("Enter search query: ").strip()
                    results = self.search_similar_code(query, where_filter=filters)
                    self._display_results(results)
            
            elif choice == '3':
                node_type = input("Enter node type (method/class/function): ").strip().lower()
                filters = {"node_type": node_type}
                query = input("Enter search query: ").strip()
                results = self.search_similar_code(query, where_filter=filters)
                self._display_results(results)
            
            elif choice == '4':
                stats = self.vector_store.get_collection_stats()
                print(f"\nCollection Statistics:")
                print(json.dumps(stats, indent=2))
            
            elif choice == '5':
                print("Exiting...")
                break
    
    def _display_results(self, results: dict):
        """Display search results in readable format"""
        if not results or 'documents' not in results:
            print("No results found.")
            return
        
        print(f"\nFound {len(results['documents'][0])} results:")
        print("-" * 80)
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"\nResult {i} (Similarity: {1-distance:.3f}):")
            print(f"File: {metadata.get('file_path', 'N/A')}")
            print(f"Type: {metadata.get('node_type', 'N/A')}")
            print(f"Name: {metadata.get('name', 'N/A')}")
            print(f"Language: {metadata.get('language', 'N/A')}")
            print(f"\nContent preview:")
            print("-" * 40)
            print(doc[:500] + "..." if len(doc) > 500 else doc)
            print("-" * 40)