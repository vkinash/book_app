from typing import List, Optional, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from settings import settings


class VectorStore:
    """
    ChromaDB vector store client for storing and retrieving book embeddings.
    """
    
    def __init__(
        self,
        collection_name: str = "books",
        persist_directory: Optional[str] = None,
        embedding_function: Optional[Embeddings] = None
    ):
        """
        Initialize ChromaDB vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist data (None = in-memory)
            embedding_function: LangChain embedding function
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or getattr(
            settings, "chroma_persist_dir", "./chroma_db"
        )
        
        # Create persist directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Store embedding function
        self.embedding_function = embedding_function
        
        # Initialize LangChain Chroma wrapper
        self._vectorstore: Optional[Chroma] = None
    
    @property
    def vectorstore(self) -> Chroma:
        """
        Get LangChain Chroma vectorstore (lazy initialization).
        
        Returns:
            LangChain Chroma vectorstore instance
        """
        if self._vectorstore is None:
            if self.embedding_function is None:
                raise ValueError("Embedding function must be set before using vectorstore")
            
            self._vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=self.persist_directory
            )
        return self._vectorstore
    
    def set_embedding_function(self, embedding_function: Embeddings) -> None:
        """
        Set the embedding function.
        
        Args:
            embedding_function: LangChain embedding function
        """
        self.embedding_function = embedding_function
        self._vectorstore = None  # Reset to force recreation
    
    def add_documents(
        self,
        documents: List[Document],
        book_id: Optional[str] = None,
        **kwargs
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of LangChain Document objects
            book_id: Optional book identifier for metadata filtering
            **kwargs: Additional arguments for add_documents
            
        Returns:
            List of document IDs
        """
        # Add book_id to metadata if provided
        if book_id:
            for doc in documents:
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata["book_id"] = book_id
        
        return self.vectorstore.add_documents(documents, **kwargs)
    
    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter (e.g., {"book_id": "book1.epub"})
            **kwargs: Additional search parameters
            
        Returns:
            List of similar documents
        """
        return self.vectorstore.similarity_search(
            query,
            k=k,
            filter=filter,
            **kwargs
        )
    
    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[tuple[Document, float]]:
        """
        Search for similar documents with similarity scores.
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional metadata filter
            **kwargs: Additional search parameters
            
        Returns:
            List of tuples (document, score)
        """
        return self.vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter=filter,
            **kwargs
        )
    
    def delete_book(self, book_id: str) -> None:
        """
        Delete all documents for a specific book.
        
        Args:
            book_id: Book identifier
        """
        # Get collection
        collection = self.client.get_collection(self.collection_name)
        
        # Get all documents with this book_id
        results = collection.get(
            where={"book_id": book_id}
        )
        
        if results["ids"]:
            collection.delete(ids=results["ids"])
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection.
        
        Returns:
            Dictionary with collection information
        """
        collection = self.client.get_collection(self.collection_name)
        return {
            "collection_name": self.collection_name,
            "count": collection.count(),
            "persist_directory": self.persist_directory
        }
