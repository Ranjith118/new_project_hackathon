"""Document processing service for loading and extracting text from various file formats."""
import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

try:
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        CSVLoader,
        UnstructuredPDFLoader
    )
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    Document = None


class DocumentProcessor:
    """Handles document loading, text extraction, and chunking."""
    
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if LANGCHAIN_AVAILABLE:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        else:
            self.text_splitter = None
    
    def load_document(self, file_path: str) -> List:
        """
        Load a document from file path based on file extension.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required for document processing. Install with: pip install langchain langchain-community")
        
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension == '.pdf':
            return self._load_pdf(file_path)
        elif extension == '.txt':
            return self._load_txt(file_path)
        elif extension == '.csv':
            return self._load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def _load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF document using PyPDFLoader."""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            return self._clean_documents(documents)
        except Exception as e:
            # Try fallback loader
            try:
                loader = UnstructuredPDFLoader(file_path, mode="elements")
                documents = loader.load()
                return self._clean_documents(documents)
            except Exception as e2:
                raise RuntimeError(f"Failed to load PDF: {str(e)}, fallback error: {str(e2)}")
    
    def _load_txt(self, file_path: str) -> List[Document]:
        """Load text document."""
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
            return self._clean_documents(documents)
        except Exception as e:
            # Try with different encoding
            try:
                loader = TextLoader(file_path, encoding='latin-1')
                documents = loader.load()
                return self._clean_documents(documents)
            except Exception as e2:
                raise RuntimeError(f"Failed to load text file: {str(e)}")
    
    def _load_csv(self, file_path: str) -> List[Document]:
        """Load CSV document as text."""
        try:
            loader = CSVLoader(file_path)
            documents = loader.load()
            return self._clean_documents(documents)
        except Exception as e:
            raise RuntimeError(f"Failed to load CSV: {str(e)}")
    
    def _clean_documents(self, documents: List[Document]) -> List[Document]:
        """Clean extracted text by removing noise and normalizing."""
        cleaned = []
        for doc in documents:
            # Extract page number if available
            page_number = self._extract_page_number(doc.metadata)
            
            # Clean the text content
            cleaned_text = self._clean_text(doc.page_content)
            
            if cleaned_text.strip():
                cleaned_doc = Document(
                    page_content=cleaned_text,
                    metadata={
                        **doc.metadata,
                        'page_number': page_number,
                        'cleaned_at': datetime.now().isoformat()
                    }
                )
                cleaned.append(cleaned_doc)
        
        return cleaned
    
    def _extract_page_number(self, metadata: Dict) -> Optional[int]:
        """Extract page number from metadata."""
        if 'page' in metadata:
            return int(metadata['page'])
        if 'source' in metadata:
            # Try to extract from filename if it contains page info
            pass
        return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause issues
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        
        # Remove leading/trailing whitespace from lines
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        
        # Remove very short lines that are likely noise
        cleaned_lines = [
            line for line in cleaned_lines 
            if len(line) > 3 or line == ''
        ]
        
        return '\n'.join(cleaned_lines).strip()
    
    def chunk_documents(
        self, 
        documents: List[Document], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Split documents into chunks with metadata.
        
        Args:
            documents: List of LangChain Document objects
            metadata: Additional metadata to attach to all chunks
            
        Returns:
            List of chunked Document objects
        """
        chunks = self.text_splitter.split_documents(documents)
        
        # Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata = {
                **chunk.metadata,
                **(metadata or {}),
                'chunk_id': str(uuid.uuid4()),
                'chunk_index': i,
                'total_chunks': len(chunks),
                'chunked_at': datetime.now().isoformat()
            }
        
        return chunks
    
    def process_file(
        self, 
        file_path: str, 
        document_type: str,
        document_name: str,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Complete pipeline: load, clean, and chunk a document.
        
        Args:
            file_path: Path to the document file
            document_type: Type of document (manual, sop, maintenance_log, failure_report)
            document_name: Name of the document
            additional_metadata: Additional metadata to attach
            
        Returns:
            List of chunked Document objects ready for embedding
        """
        # Load the document
        documents = self.load_document(file_path)
        
        # Prepare metadata
        base_metadata = {
            'document_name': document_name,
            'document_type': document_type,
            'file_path': file_path,
            'uploaded_at': datetime.now().isoformat()
        }
        
        if additional_metadata:
            base_metadata.update(additional_metadata)
        
        # Chunk the documents
        chunks = self.chunk_documents(documents, base_metadata)
        
        return chunks
    
    @staticmethod
    def get_supported_extensions() -> List[str]:
        """Return list of supported file extensions."""
        return ['.pdf', '.txt', '.csv']


class DocumentMetadata:
    """Stores metadata for processed documents."""
    
    def __init__(
        self,
        document_id: str,
        document_name: str,
        document_type: str,
        file_path: str,
        file_size: int,
        total_chunks: int,
        chunk_size: int,
        processing_status: str = "pending",
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.document_id = document_id
        self.document_name = document_name
        self.document_type = document_type
        self.file_path = file_path
        self.file_size = file_size
        self.total_chunks = total_chunks
        self.chunk_size = chunk_size
        self.processing_status = processing_status
        self.error_message = error_message
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'document_id': self.document_id,
            'document_name': self.document_name,
            'document_type': self.document_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'total_chunks': self.total_chunks,
            'chunk_size': self.chunk_size,
            'processing_status': self.processing_status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentMetadata':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        data['updated_at'] = datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        return cls(**data)