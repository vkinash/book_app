from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from settings import settings


class TextProcessor:
    """
    Service for processing and chunking text documents.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize text processor.
        
        Args:
            chunk_size: Maximum size of chunks (in characters)
            chunk_overlap: Overlap between chunks
            separators: Custom separators for splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Default separators: try to split on paragraphs, sentences, then words
        if separators is None:
            separators = ["\n\n", "\n", ". ", " ", ""]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len
        )
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Split text into chunks and create Document objects.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to add to all chunks
            
        Returns:
            List of Document objects
        """
        chunks = self.text_splitter.split_text(text)
        
        documents = []
        for i, chunk in enumerate(chunks):
            doc_metadata = {"chunk_index": i}
            if metadata:
                doc_metadata.update(metadata)
            
            documents.append(
                Document(
                    page_content=chunk,
                    metadata=doc_metadata
                )
            )
        
        return documents
