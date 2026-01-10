# LangGraph workflow module
from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator
import logging
from code_parser import AndroidCodeParser
from embeddings import CodeEmbeddingsGenerator
from vector_store import ChromaVectorStore
from config import Config

logger = logging.getLogger(__name__)

class PipelineState(TypedDict):
    """State definition for the pipeline"""
    project_path: str
    parsed_chunks: List[Dict[str, Any]]
    documents: List[str]
    embeddings: List[List[float]]
    metadatas: List[Dict[str, Any]]
    storage_success: bool
    collection_stats: Dict[str, Any]

class AndroidCodePipeline:
    def __init__(self):
        """Initialize the pipeline components"""
        self.config = Config()
        self.parser = AndroidCodeParser()
        self.embedding_gen = CodeEmbeddingsGenerator()
        self.vector_store = ChromaVectorStore()
        
        # Create the workflow graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self):
        """Create LangGraph workflow"""
        workflow = StateGraph(PipelineState)
        
        # Add nodes
        workflow.add_node("parse_code", self.parse_code_node)
        workflow.add_node("generate_embeddings", self.generate_embeddings_node)
        workflow.add_node("store_in_vector_db", self.store_vector_db_node)
        workflow.add_node("generate_report", self.generate_report_node)
        
        # Define edges
        workflow.add_edge("parse_code", "generate_embeddings")
        workflow.add_edge("generate_embeddings", "store_in_vector_db")
        workflow.add_edge("store_in_vector_db", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Set entry point
        workflow.set_entry_point("parse_code")
        
        return workflow.compile()
    
    def parse_code_node(self, state: PipelineState) -> PipelineState:
        """Parse Android source code using Tree-sitter"""
        logger.info(f"Parsing code from: {state['project_path']}")
        
        try:
            parsed_chunks = self.parser.traverse_directory(state['project_path'])
            return {
                **state,
                "parsed_chunks": parsed_chunks
            }
        except Exception as e:
            logger.error(f"Error in parse_code_node: {e}")
            return {**state, "parsed_chunks": []}
    
    def generate_embeddings_node(self, state: PipelineState) -> PipelineState:
        """Generate embeddings for parsed code chunks"""
        if not state['parsed_chunks']:
            logger.warning("No parsed chunks to generate embeddings for")
            return {**state, "documents": [], "embeddings": []}
        
        logger.info(f"Generating embeddings for {len(state['parsed_chunks'])} chunks")
        
        documents = []
        metadatas = []
        
        for chunk in state['parsed_chunks']:
            # Prepare document text for embedding
            document_text = self.embedding_gen.prepare_text_for_embedding(chunk)
            documents.append(document_text)
            
            # Prepare metadata
            metadata = {
                'file_path': chunk.get('relative_path', ''),
                'language': chunk.get('language', ''),
                'node_type': chunk.get('node_type', ''),
                'name': chunk.get('name', ''),
                'start_line': chunk.get('start_point', (0, 0))[0],
                'end_line': chunk.get('end_point', (0, 0))[0]
            }
            metadatas.append(metadata)
        
        # Generate embeddings in batch
        embeddings = self.embedding_gen.batch_generate_embeddings(documents)
        
        return {
            **state,
            "documents": documents,
            "embeddings": embeddings,
            "metadatas": metadatas
        }
    
    def store_vector_db_node(self, state: PipelineState) -> PipelineState:
        """Store embeddings in ChromaDB"""
        if not state['embeddings']:
            logger.warning("No embeddings to store")
            return {**state, "storage_success": False}
        
        logger.info(f"Storing {len(state['embeddings'])} embeddings in ChromaDB")
        
        success = self.vector_store.store_embeddings(
            embeddings=state['embeddings'],
            documents=state['documents'],
            metadatas=state['metadatas']
        )
        
        return {
            **state,
            "storage_success": success
        }
    
    def generate_report_node(self, state: PipelineState) -> PipelineState:
        """Generate pipeline execution report"""
        collection_stats = self.vector_store.get_collection_stats()
        
        report = {
            "total_chunks_parsed": len(state.get('parsed_chunks', [])),
            "embeddings_generated": len(state.get('embeddings', [])),
            "storage_success": state.get('storage_success', False),
            "collection_stats": collection_stats
        }
        
        logger.info(f"Pipeline completed. Report: {report}")
        
        return {
            **state,
            "collection_stats": collection_stats
        }
    
    def run(self, project_path: str) -> PipelineState:
        """Execute the complete pipeline"""
        initial_state = PipelineState(
            project_path=project_path,
            parsed_chunks=[],
            documents=[],
            embeddings=[],
            metadatas=[],
            storage_success=False,
            collection_stats={}
        )
        
        return self.workflow.invoke(initial_state)