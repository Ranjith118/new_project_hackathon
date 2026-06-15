"""ChromaDB vector database service for storing and retrieving document embeddings."""
import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False

try:
    from chromadb.api.models.Collection import Collection
except Exception:
    Collection = None

try:
    from langchain.schema import Document
except Exception:
    try:
        from langchain_core.documents import Document
    except Exception:
        Document = None

from app.services.embeddings.embeddings import get_embedding_service


class ChromaVectorStore:
    """
    Vector database service using ChromaDB for storing and retrieving document embeddings.
    
    Manages collections, CRUD operations, and similarity search.
    """
    
    COLLECTION_NAME = "maintenance_knowledge_base"
    DEFAULT_PERSIST_DIRECTORY = "./chroma_db"
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = COLLECTION_NAME,
        embedding_service: Optional[Any] = None
    ):
        """
        Initialize the ChromaDB vector store.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection
            embedding_service: Embedding service instance
        """
        self.persist_directory = persist_directory or self.DEFAULT_PERSIST_DIRECTORY
        self.collection_name = collection_name
        
        # Create persist directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding service
        self.embedding_service = embedding_service
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self) -> Collection:
        """Get or create the maintenance knowledge base collection."""
        try:
            return self.client.get_collection(name=self.collection_name)
        except Exception:
            # Create collection with metadata
            return self.client.create_collection(
                name=self.collection_name,
                metadata={
                    "description": "Maintenance Wizard Knowledge Base",
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
            )
    
    def add_documents(
        self,
        documents: List[Document],
        embeddings: Optional[np.ndarray] = None,
        regenerate_embeddings: bool = True
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of LangChain Document objects
            embeddings: Pre-computed embeddings (optional)
            regenerate_embeddings: Whether to regenerate embeddings
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Generate embeddings if not provided
        if embeddings is None or regenerate_embeddings:
            if self.embedding_service is None:
                self.embedding_service = get_embedding_service()
            embeddings = self.embedding_service.embed_documents(documents)
        
        # Prepare data for ChromaDB
        ids = []
        documents_texts = []
        metadatas = []
        embeddings_list = []
        
        for i, doc in enumerate(documents):
            doc_id = doc.metadata.get('chunk_id', str(uuid.uuid4()))
            ids.append(doc_id)
            documents_texts.append(doc.page_content)
            
            # Add metadata with source tracking
            metadata = {
                **doc.metadata,
                'added_at': datetime.now().isoformat()
            }
            metadatas.append(metadata)
            
            # Convert to list if numpy array
            if hasattr(embeddings[i], 'tolist'):
                embeddings_list.append(embeddings[i].tolist())
            else:
                embeddings_list.append(embeddings[i])
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=documents_texts,
            metadatas=metadatas,
            embeddings=embeddings_list
        )
        
        return ids
    
    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add texts directly to the vector store.
        
        Args:
            texts: List of text strings
            metadatas: List of metadata dicts
            ids: List of document IDs
            
        Returns:
            List of document IDs
        """
        if not texts:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Generate embeddings
        if self.embedding_service is None:
            self.embedding_service = get_embedding_service()
        embeddings = self.embedding_service.embed_texts(texts)
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{"added_at": datetime.now().isoformat()} for _ in texts]
        
        # ensure plain lists
        embeddings_list = [e.tolist() if hasattr(e, 'tolist') else e for e in embeddings]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings_list
        )
        
        return ids
    
    def similarity_search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search on the vector store.
        
        Args:
            query: Query string
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        if self.embedding_service is None:
            self.embedding_service = get_embedding_service()
        query_embedding = self.embedding_service.embed_query(query)
        # ensure it's a plain list (not numpy array)
        if hasattr(query_embedding, 'tolist'):
            query_embedding = query_embedding.tolist()

        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            # Convert L2 distance to a 0–1 similarity score.
            # 1/(1+d) is always positive, equals 1 when d=0 and approaches 0 as d grows.
            score = 1.0 / (1.0 + distance)
            formatted_results.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': distance,
                'score': score
            })
        
        return formatted_results
    
    def get_document_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document dict or None if not found
        """
        try:
            result = self.collection.get(
                ids=[document_id],
                include=["documents", "metadatas"]
            )
            
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'content': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception:
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the vector store.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception:
            return False
    
    def delete_documents_by_filter(self, where: Dict[str, Any]) -> int:
        """
        Delete documents matching a filter.
        
        Args:
            where: Metadata filter
            
        Returns:
            Number of deleted documents
        """
        try:
            # Get matching documents first
            result = self.collection.get(
                where=where,
                include=["ids"]
            )
            
            if result['ids']:
                count = len(result['ids'])
                self.collection.delete(ids=result['ids'])
                return count
            return 0
        except Exception:
            return 0
    
    def update_document(
        self,
        document_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document in the vector store.
        
        Args:
            document_id: Document ID
            content: New content (optional)
            metadata: New metadata (optional)
            
        Returns:
            True if updated, False otherwise
        """
        try:
            update_data = {}
            if content is not None:
                update_data['documents'] = [content]
            if metadata is not None:
                update_data['metadatas'] = [metadata]
            
            if update_data:
                self.collection.update(
                    ids=[document_id],
                    **update_data
                )
            return True
        except Exception:
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            return {
                'name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory
            }
        except Exception as e:
            return {
                'name': self.collection_name,
                'error': str(e)
            }

    def get_all_texts(self, limit: int = 2000) -> list:
        """Retrieve all stored document texts for embedder warm-up."""
        try:
            result = self.collection.get(
                limit=limit,
                include=["documents"]
            )
            return result.get("documents", [])
        except Exception:
            return []
    
    def search_by_document_type(
        self,
        query: str,
        document_type: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents filtered by document type.
        
        Args:
            query: Query string
            document_type: Type of document to filter
            n_results: Number of results
            
        Returns:
            List of matching documents
        """
        return self.similarity_search(
            query=query,
            n_results=n_results,
            where={"document_type": document_type}
        )
    
    def search_by_source(
        self,
        query: str,
        source: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents filtered by source.
        
        Args:
            query: Query string
            source: Source document name
            n_results: Number of results
            
        Returns:
            List of matching documents
        """
        return self.similarity_search(
            query=query,
            n_results=n_results,
            where={"source": source}
        )
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            True if cleared, False otherwise
        """
        try:
            self.collection.delete(where={})
            return True
        except Exception:
            return False
    
    def reset_collection(self) -> None:
        """Delete and recreate the collection."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        self.collection = self._get_or_create_collection()


# Singleton instance
_vector_store: Optional[ChromaVectorStore] = None


def get_vector_store() -> ChromaVectorStore:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


def reset_vector_store() -> None:
    """Reset the global vector store instance."""
    global _vector_store
    _vector_store = None