from typing import List, Optional, Dict, Any
from pathlib import Path
from langchain_core.documents import Document
from api.services.epub import EPUBData
from core.text_processor import TextProcessor
from core.embeddings import EmbeddingService
from core.vector_store import VectorStore
from core.llm_client import LLMClient


class RAGService:
    """
    Main RAG service for processing books and answering questions.
    """
    
    def __init__(
        self,
        embedding_model: str = "embeddinggemma",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize RAG service.
        
        Args:
            embedding_model: Ollama embedding model name
            chunk_size: Text chunk size
            chunk_overlap: Chunk overlap size
        """
        self.epub_service = EPUBData()
        self.text_processor = TextProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.embedding_service = EmbeddingService(model_name=embedding_model)
        self.vector_store = VectorStore()
        self.vector_store.set_embedding_function(self.embedding_service.embeddings)
    
    async def process_book(self, epub_path: str) -> Dict[str, Any]:
        """
        Process a book: extract text, chunk, embed, and store in vector DB.
        
        Args:
            epub_path: Path to EPUB file
            
        Returns:
            Dictionary with processing results
        """
        # Extract text
        text = await self.epub_service.extract_text_from_book(epub_path)
        
        # Get book identifier
        book_id = Path(epub_path).stem
        
        # Chunk text
        documents = self.text_processor.chunk_text(
            text,
            metadata={"book_id": book_id, "source": epub_path}
        )
        
        # Add to vector store
        doc_ids = self.vector_store.add_documents(
            documents,
            book_id=book_id
        )
        
        return {
            "book_id": book_id,
            "total_chunks": len(documents),
            "document_ids": doc_ids
        }
    
    def search(
        self,
        query: str,
        book_id: Optional[str] = None,
        k: int = 4
    ) -> List[Document]:
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            book_id: Optional book ID to filter results
            k: Number of results
            
        Returns:
            List of relevant documents
        """
        filter_dict = {"book_id": book_id} if book_id else None
        return self.vector_store.similarity_search(
            query,
            k=k,
            filter=filter_dict
        )
    
    async def answer_question(
        self,
        question: str,
        book_id: Optional[str] = None,
        llm_client: Optional[LLMClient] = None
    ) -> str:
        """
        Answer a question using RAG.
        
        Args:
            question: Question to answer
            book_id: Optional book ID to search in
            llm_client: Optional LLM client (uses default if not provided)
            
        Returns:
            Answer string
        """
        # Search for relevant context
        context_docs = self.search(question, book_id=book_id, k=4)
        
        # Build context from documents
        context = "\n\n".join([doc.page_content for doc in context_docs])
        
        # Create prompt
        prompt = f"""Answer the following question based on the provided context from the book.

Context:
{context}

Question: {question}

Answer:"""
        
        # Get LLM client
        if llm_client is None:
            llm_client = LLMClient.from_settings()
        
        # Generate answer
        answer = llm_client.llm.invoke(prompt)
        return answer
