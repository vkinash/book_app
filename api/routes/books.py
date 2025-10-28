import ebooklib
import os
import uuid
import xml.etree.ElementTree as ET
import re


from fastapi.responses import Response, PlainTextResponse, HTMLResponse
import zipfile
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, Query, HTTPException
from ebooklib import epub
from api.services.epub import EPUBData
from bs4 import BeautifulSoup



router = APIRouter(
    prefix="/book",
    tags=["books"]
)


@router.get("/epub_book/")
async def get_epub_book_data(file_name: str):
    # print(epub_file.filename)
    # book = epub.read_epub(f"books_test/{epub_file.filename}")
    # print(book.get_metadata('DC', 'title'))
    # print(book.get_metadata('DC', 'creator'))
    # print(book.get_metadata('DC', 'identifier'))
    # print(book.get_metadata('DC', 'description'))
    # print(book.get_metadata('DC', 'coverage'))
    # print(book.get_metadata('DC', 'publisher'))
    # print(book.get_metadata('DC', 'contributor'))
    # l = list()
    # for item in book.get_items():
    #     if item.get_type() == ebooklib.ITEM_DOCUMENT:
    #         print('==================================')
    #         print('NAME : ', item.get_name())
    #         print('----------------------------------')
    #         # print(item.get_content())
    #         # print('==================================')
    #         l.append((item.get_name(), item.get_content()))
    # return {"book": l}
    # print("m", book.metadata)
    # print("spine", book.spine)
    # print("toc", book.toc)

    # for x in book.get_items_of_type(ebooklib.ITEM_IMAGE):
    #     print("ITEM_IMAGE", x)
    # SAVE_DIR = "test"
    # for i, item in enumerate(book.get_items_of_type(ebooklib.ITEM_IMAGE)):
    #     file_name = item.file_name.split("/")[-1] or f"image_{i}.jpg"
    #     save_path = os.path.join(SAVE_DIR, file_name)
    #
    #     with open(save_path, "wb") as img_file:
    #         img_file.write(item.get_content())
    #
    #     print(f"Saved image: {save_path}")
    #
    # for x in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
    #     print("ITEM_DOCUMENT", x.content.decode("utf-8"))


    book = EPUBData(file_path=file_name)
    images = book.list_of_images()
    docs = book.list_of_documents()
    # content = list([(str(doc), soup(book.get_documents_content(doc), "lxml").get_text()) for doc in docs])
    content = list([book.get_documents_content(doc) for doc in docs])

    return Response(content=content[13], media_type="application/xhtml+xml")


BOOKS_DIR = Path("books_stored")



def get_container_xml(epub_path: str) -> str:
    with zipfile.ZipFile(epub_path, 'r') as z:
        if 'META-INF/container.xml' not in z.namelist():
            raise FileNotFoundError("container.xml not found in EPUB")
        return z.read('META-INF/container.xml').decode('utf-8')

def get_opf_path(container_xml: str) -> str:
    soup = BeautifulSoup(container_xml, 'xml')
    rootfile = soup.find('rootfile')
    if not rootfile or not rootfile.has_attr('full-path'):
        raise ValueError("OPF path not found in container.xml")
    return rootfile['full-path']

def get_spine_order(epub_path: str, opf_path: str) -> list[str]:
    with zipfile.ZipFile(epub_path, 'r') as z:
        opf_content = z.read(opf_path).decode('utf-8')

    soup = BeautifulSoup(opf_content, 'xml')

    # Build manifest mapping (id → href)
    manifest = {item['id']: os.path.join(os.path.dirname(opf_path), item['href'])
                for item in soup.find_all('item')}
    # Build ordered list via spine
    order = [manifest[itemref['idref']] for itemref in soup.find_all('itemref')]
    return order


def rewrite_resource_urls(html_content: str, file_path: str, current_xhtml_path: str) -> str:
    """
    Rewrite resource URLs in XHTML content to point to the epub-resource endpoint.

    Args:
        html_content: The XHTML content
        file_path: Path to the EPUB file
        current_xhtml_path: Path of the current XHTML file within the EPUB
    """
    file_name = os.path.basename(file_path)

    # Get the directory of the current XHTML file to resolve relative paths
    current_dir = os.path.dirname(current_xhtml_path)

    def resolve_path(match):
        """Resolve relative paths and rewrite to endpoint URL."""
        attr_name = match.group(1)  # 'href' or 'src'
        original_path = match.group(2)  # the actual path
        print("0", match.group(0),"1",  match.group(1), "2",  match.group(2))
        # Skip external URLs and data URIs
        if original_path.startswith(('http://', 'https://', 'data:', '//')):
            return match.group(0)

        # Resolve relative path
        if current_dir and not original_path.startswith('/'):
            # Combine current directory with relative path and normalize
            resolved = os.path.normpath(os.path.join(current_dir, original_path))
            # Convert Windows path separators to forward slashes
            resolved = resolved.replace('\\', '/')
        else:
            resolved = original_path.lstrip('/')

        # Create new URL pointing to our endpoint
        # Use &amp; instead of & for XHTML compliance
        new_url = f"/book/epub-resource?file_path={quote(file_path)}&amp;resource_path={quote(resolved)}"

        return f'{attr_name}="{new_url}"'

    # Rewrite href and src attributes
    # Pattern captures: (href|src)=["'](path)["']
    html_content = re.sub(
        r'(href|src)=["\']((?!http://|https://|data:|//)[^"\']+)["\']',
        resolve_path,
        html_content
    )

    return html_content

def read_epub_file(epub_path: str, internal_path: str) -> str:
    with zipfile.ZipFile(epub_path, 'r') as z:
        return z.read(internal_path)

@router.get("/first-chapter", response_class=HTMLResponse)
def get_first_chapter(file_path: str = Query(...)):

    # 1) Copy file into books_test
    file_name = os.path.basename(file_path)
    saved_path = os.path.join(BOOKS_DIR, file_name)
    with open(file_path, 'rb') as src, open(saved_path, 'wb') as dst:
        dst.write(src.read())

    # 2) Read container.xml
    container_xml = get_container_xml(saved_path)

    # 3) Get path to content.opf
    opf_path = get_opf_path(container_xml)

    # 4) Get ordered XHTML files
    ordered_files = get_spine_order(saved_path, opf_path)

    # 5) Read first file content
    cur_file = ordered_files[4]
    first_file_content = read_epub_file(saved_path, cur_file)
    print(ordered_files)
    # 6) Rewrite resource URLs to point to our endpoint
    first_file_content_str = first_file_content.decode('utf-8') if isinstance(first_file_content,
                                                                              bytes) else first_file_content
    modified_content = rewrite_resource_urls(first_file_content_str, file_path, cur_file)

    # print(saved_path, os.path.exists(saved_path), os.path.getsize(saved_path), ordered_files[3])

    return Response(content=modified_content, media_type="application/xhtml+xml")


# Endpoint to serve resources from EPUB
@router.get("/epub-resource")
def get_epub_resource(
        file_path: str = Query(...),
        resource_path: str = Query(...)
):
    """Serve a resource (CSS, image, etc.) from an EPUB file."""
    file_name = os.path.basename(file_path)
    saved_path = os.path.join(BOOKS_DIR, file_name)

    # Read the resource from the EPUB
    resource_content = read_epub_file(saved_path, resource_path)

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
