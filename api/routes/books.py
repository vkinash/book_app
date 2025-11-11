import os

from fastapi.responses import Response, HTMLResponse
from fastapi import APIRouter, UploadFile, Query, HTTPException, File
from api.services.epub import EPUBData
from settings import settings
from api.utils.books_navigation import add_navigation_buttons


router = APIRouter(
    prefix="/book",
    tags=["books"]
)


# Endpoint to serve resources from EPUB
@router.get("/epub_resource")
async def get_epub_resource(
        file_path: str = Query(...),
        resource_path: str = Query(...)
):
    """Serve a resource (CSS, image, etc.) from an EPUB file."""
    file_name = os.path.basename(file_path)
    saved_path = os.path.join(settings.books_path, file_name)

    # Read the resource from the EPUB
    epub_service = EPUBData()
    resource_content = await epub_service.read_epub_file(saved_path, resource_path)

    # Determine media type based on file extension
    ext = resource_path.lower().split('.')[-1]
    media_types = {
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
    media_type = media_types.get(ext, 'application/octet-stream')

    return Response(content=resource_content, media_type=media_type)


# 1) Upload and store book
@router.post("/upload_book")
async def upload_book(file: UploadFile = File(...)):
    """Upload an EPUB file and store it in the books directory."""

    # Validate file extension
    if not file.filename.endswith('.epub'):
        raise HTTPException(status_code=400, detail="Only EPUB files are allowed")

    epub_service = EPUBData()
    # Save file to books_stored directory
    saved_path = await epub_service.upload_book(file)

    return {
        "message": "Book uploaded successfully",
        "filename": file.filename,
        "path": saved_path
    }


# 2) Get list of stored books
@router.get("/stored_books")
def get_stored_books():
    """Return list of all books stored in the books directory."""
    book_path = settings.books_path
    if not os.path.exists(book_path):
        return {"books": []}

    epub_service = EPUBData()
    # Get all .epub files in the directory
    books = epub_service.get_books()

    return {"books": books}


@router.get("/chapter", response_class=HTMLResponse)
async def get_chapter(
        filename: str = Query(...),
        chapter_index: int = Query(0, ge=0)
):
    """Return a specific chapter of a stored book by index with navigation buttons."""

    # Get the saved path
    saved_path = os.path.join(settings.books_path, filename)

    # Check if file exists
    if not os.path.exists(saved_path):
        raise HTTPException(status_code=404, detail="Book not found")

    epub_service = EPUBData()
    # Read container.xml
    container_xml = await epub_service.read_epub_file(
        epub_path=saved_path,
        internal_path='META-INF/container.xml'
    )
    container_xml = container_xml.decode('utf-8')

    # Get path to content.opf
    opf_path = await epub_service.get_opf_path(container_xml)

    # Get ordered XHTML files
    ordered_files = await epub_service.get_spine_order(saved_path, opf_path)

    # Validate chapter_index
    if chapter_index >= len(ordered_files):
        raise HTTPException(
            status_code=404,
            detail=f"Chapter index {chapter_index} out of range. Book has {len(ordered_files)} chapters."
        )

    # Read the requested chapter
    cur_file = ordered_files[chapter_index]
    chapter_content = await epub_service.read_epub_file(saved_path, cur_file)

    # Rewrite resource URLs to point to our endpoint
    chapter_content_str = chapter_content.decode('utf-8') if isinstance(
        chapter_content, bytes
    ) else chapter_content
    modified_content = await epub_service.rewrite_resource_urls(chapter_content_str, saved_path, cur_file)

    # Add navigation buttons
    modified_content = add_navigation_buttons(
        modified_content,
        filename,
        chapter_index,
        len(ordered_files)
    )

    return Response(content=modified_content, media_type="application/xhtml+xml")


# Optional: Add an endpoint to get total chapter count
@router.get("/chapter_count")
async def get_chapter_count(filename: str = Query(...)):
    """Return the total number of chapters in a book."""

    saved_path = os.path.join(settings.books_path, filename)

    if not os.path.exists(saved_path):
        raise HTTPException(status_code=404, detail="Book not found")

    epub_service = EPUBData()

    # Read container.xml
    container_xml = await epub_service.read_epub_file(
        epub_path=saved_path,
        internal_path='META-INF/container.xml'
    )
    container_xml = container_xml.decode('utf-8')
    # Get path to content.opf
    opf_path = await epub_service.get_opf_path(container_xml)
    # Get ordered XHTML files
    ordered_files = await epub_service.get_spine_order(saved_path, opf_path)

    return {
        "filename": filename,
        "total_chapters": len(ordered_files),
        "chapters": ordered_files  # Optional: return list of chapter file names
    }