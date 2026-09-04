import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse, Response
from ollama import ResponseError
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_dev_user
from api.services.book_service import book_file_path, create_book, get_book, list_books
from api.services.epub import EPUBData
from api.utils.books_navigation import add_navigation_buttons
from core.rag_service import RAGService
from db.models.user import User
from db.session import get_async_session
from settings import settings

router = APIRouter(
    prefix="/book",
    tags=["books"],
)

rag_service = RAGService()

MEDIA_TYPES = {
    'css': 'text/css',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'svg': 'image/svg+xml',
    'woff': 'font/woff',
    'woff2': 'font/woff2',
    'ttf': 'font/ttf',
    'otf': 'font/otf',
}


def _media_type_for(resource_path: str) -> str:
    ext = resource_path.lower().split('.')[-1]
    return MEDIA_TYPES.get(ext, 'application/octet-stream')


async def _resolve_book_path(
    session: AsyncSession,
    user: User,
    book_id: uuid.UUID
) -> tuple[str, str | None, str | None]:
    """
    Resolve EPUB file path and navigation keys.
    Returns (saved_path, nav_filename, nav_book_id).
    """
    book = await get_book(session, book_id, user.id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    saved_path = str(book_file_path(book))
    if not os.path.exists(saved_path):
        raise HTTPException(status_code=404, detail="Book file not found on disk")
    return saved_path, None, str(book.id)


@router.get("/epub_resource")
async def get_epub_resource(
    resource_path: str = Query(...),
    book_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Serve a resource (CSS, image, etc.) from an EPUB file."""
    saved_path, _, _ = await _resolve_book_path(session, user, book_id, None)

    epub_service = EPUBData()
    resource_content = await epub_service.read_epub_file(saved_path, resource_path)
    return Response(content=resource_content, media_type=_media_type_for(resource_path))


@router.post("/upload_book")
async def upload_book(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Upload an EPUB, store metadata in DB, and process for RAG."""
    if not file.filename or not file.filename.endswith('.epub'):
        raise HTTPException(status_code=400, detail="Only EPUB files are allowed")

    book_uuid = uuid.uuid4()
    destination = settings.books_path / f"{book_uuid}.epub"

    epub_service = EPUBData()
    saved_path = await epub_service.upload_book(file, destination)
    metadata = await epub_service.extract_metadata(saved_path)

    book = await create_book(
        session=session,
        user=user,
        filename=file.filename,
        title=metadata.get("title"),
        author=metadata.get("author"),
        book_id=book_uuid,
    )

    book_id_str = str(book.id)
    try:
        processing_result = await rag_service.process_book(saved_path, book_id=book_id_str)
        return {
            "message": "Book uploaded and processed successfully",
            "id": book_id_str,
            "filename": book.filename,
            "title": book.title,
            "author": book.author,
            "total_chunks": processing_result["total_chunks"],
        }
    except (ValueError, FileNotFoundError, OSError, ResponseError) as e:
        return {
            "message": "Book uploaded successfully but processing failed",
            "id": book_id_str,
            "filename": book.filename,
            "title": book.title,
            "author": book.author,
            "error": str(e),
            "warning": "Book may not be available for Q&A until processed",
        }


@router.get("/stored_books")
async def get_stored_books(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Return books from the database for the current dev user."""
    books = await list_books(session, user.id)
    return {
        "books": [
            {
                "id": str(book.id),
                "filename": book.filename,
                "title": book.title,
                "author": book.author,
                "format": book.format,
                "uploaded_at": book.uploaded_at.isoformat(),
            }
            for book in books
        ]
    }


@router.get("/chapter", response_class=HTMLResponse)
async def get_chapter(
    chapter_index: int = Query(0, ge=0),
    book_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Return a chapter of a stored book with navigation buttons."""
    saved_path, nav_filename, nav_book_id = await _resolve_book_path(
        session, user, book_id
    )

    epub_service = EPUBData()
    container_xml = await epub_service.read_epub_file(
        epub_path=saved_path,
        internal_path='META-INF/container.xml',
    )
    container_xml = container_xml.decode('utf-8')
    opf_path = await epub_service.get_opf_path(container_xml)
    ordered_files = await epub_service.get_spine_order(saved_path, opf_path)

    if chapter_index >= len(ordered_files):
        raise HTTPException(
            status_code=404,
            detail=f"Chapter index {chapter_index} out of range. Book has {len(ordered_files)} chapters.",
        )

    cur_file = ordered_files[chapter_index]
    chapter_content = await epub_service.read_epub_file(saved_path, cur_file)
    chapter_content_str = (
        chapter_content.decode('utf-8')
        if isinstance(chapter_content, bytes)
        else chapter_content
    )
    modified_content = await epub_service.rewrite_resource_urls(
        chapter_content_str,
        saved_path,
        cur_file,
        book_id=nav_book_id,
    )
    modified_content = add_navigation_buttons(
        modified_content,
        nav_filename or "",
        chapter_index,
        len(ordered_files),
        book_id=nav_book_id,
    )

    return Response(content=modified_content, media_type="application/xhtml+xml")


@router.get("/chapter_count")
async def get_chapter_count(
    book_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Return the total number of chapters in a book."""
    saved_path, nav_filename, nav_book_id = await _resolve_book_path(
        session, user, book_id
    )

    epub_service = EPUBData()
    container_xml = await epub_service.read_epub_file(
        epub_path=saved_path,
        internal_path='META-INF/container.xml',
    )
    container_xml = container_xml.decode('utf-8')
    opf_path = await epub_service.get_opf_path(container_xml)
    ordered_files = await epub_service.get_spine_order(saved_path, opf_path)

    return {
        "filename": nav_filename,
        "book_id": nav_book_id,
        "total_chapters": len(ordered_files),
        "chapters": ordered_files,
    }


@router.post("/process_book")
async def process_book(
    book_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Process a book for RAG."""
    saved_path, nav_filename, nav_book_id = await _resolve_book_path(
        session, user, book_id
    )
    rag_book_id = nav_book_id or Path(saved_path).stem

    try:
        processing_result = await rag_service.process_book(saved_path, book_id=rag_book_id)
        return {
            "message": "Book processed successfully",
            "filename": nav_filename,
            "book_id": processing_result["book_id"],
            "total_chunks": processing_result["total_chunks"],
        }
    except (ValueError, FileNotFoundError, OSError, ResponseError) as e:
        raise HTTPException(status_code=500, detail=f"Error processing book: {str(e)}")


@router.post("/ask")
async def ask_question(
    question: str = Query(..., description="Question to ask about the book"),
    book_id: str = Query(..., description="DB UUID"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_dev_user),
):
    """Ask a question about a book using RAG."""
    rag_book_id = book_id

    try:
        parsed_id = uuid.UUID(book_id)
        book = await get_book(session, parsed_id, user.id)
        if book is not None:
            rag_book_id = str(book.id)
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID '{book_id}' not found. Make sure the book is uploaded.",
            )
    except ValueError:
        epub_service = EPUBData()
        books = epub_service.get_books()
        book_file = None
        for book_entry in books:
            if Path(book_entry["filename"]).stem == book_id:
                book_file = book_entry
                break
        if not book_file:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ID '{book_id}' not found. Make sure the book is uploaded.",
            )

    try:
        answer = await rag_service.answer_question(question=question, book_id=rag_book_id)
        if not answer or not answer.strip():
            raise HTTPException(
                status_code=404,
                detail=f"Book '{book_id}' may not be processed yet. Please process the book first.",
            )
        return {
            "book_id": rag_book_id,
            "question": question,
            "answer": answer,
        }
    except HTTPException:
        raise
    except (ValueError, OSError) as e:
        raise HTTPException(status_code=500, detail=f"Error answering question: {str(e)}")
