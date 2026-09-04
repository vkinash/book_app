import os
import zipfile
import re
from pathlib import Path

from settings import settings
from fastapi import UploadFile
from bs4 import BeautifulSoup
from urllib.parse import quote


class EPUBData:
    """
        The class parses data from files in EPUB format using
        ebooklib library (https://docs.sourcefabric.org/projects/ebooklib/en/latest/tutorial.html#introduction).

        Attributes:
            file_name (str): path to the file with a book in epub format.
    """
    def __init__(self):
        # Reading epub file
        self.books_storage = settings.books_path

    async def upload_book(self, file: UploadFile, destination_path: Path) -> str:
        """
        Save uploaded EPUB to the given path.
        :param file: file as UploadFile obj
        :param destination_path: full path where the file should be written
        :return: path to saved file
        """
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        with open(destination_path, 'wb') as dst:
            while chunk := await file.read(settings.chunk_size):
                dst.write(chunk)

        return str(destination_path)

    @staticmethod
    async def get_opf_path(container_xml: str) -> str:
        """
        Return the path to container.xml
        :return:
        """
        soup = BeautifulSoup(container_xml, 'xml')
        rootfile = soup.find('rootfile')
        if not rootfile or not rootfile.has_attr('full-path'):
            raise ValueError("OPF path not found in container.xml")
        return rootfile['full-path']

    async def get_spine_order(self, epub_path: str, opf_path: str) -> list[str]:

        opf_content = await self.read_epub_file(epub_path=epub_path, internal_path=opf_path)
        opf_content = opf_content.decode('utf-8')

        soup = BeautifulSoup(opf_content, 'xml')

        # Build manifest mapping (id → href)
        manifest = {item['id']: os.path.join(os.path.dirname(opf_path), item['href'])
                    for item in soup.find_all('item')}
        # Build ordered list via spine
        order = [manifest[itemref['idref']] for itemref in soup.find_all('itemref')]
        return order

    async def extract_metadata(self, epub_path: str) -> dict[str, str | None]:
        """Extract title and author from EPUB OPF metadata."""
        container_xml = await self.read_epub_file(
            epub_path=epub_path,
            internal_path='META-INF/container.xml',
        )
        container_xml = container_xml.decode('utf-8')
        opf_path = await self.get_opf_path(container_xml)

        opf_content = await self.read_epub_file(epub_path=epub_path, internal_path=opf_path)
        opf_content = opf_content.decode('utf-8')
        soup = BeautifulSoup(opf_content, 'xml')

        title_tag = soup.find('dc:title') or soup.find('title')
        creator_tags = soup.find_all('dc:creator') or soup.find_all('creator')

        title = title_tag.get_text(strip=True) if title_tag else None
        author = creator_tags[0].get_text(strip=True) if creator_tags else None

        return {"title": title, "author": author}

    @staticmethod
    async def read_epub_file(epub_path: str, internal_path: str) -> str:
        with zipfile.ZipFile(epub_path, 'r') as z:
            if internal_path not in z.namelist():
                raise FileNotFoundError(f"{internal_path} not found in EPUB")
            return z.read(internal_path)

    @staticmethod
    async def rewrite_resource_urls(
        html_content: str,
        current_xhtml_path: str,
        book_id: str,
    ) -> str:
        """
        Rewrite resource URLs in XHTML content to point to the epub-resource endpoint.

        Args:
            html_content: The XHTML content
            current_xhtml_path: Path of the current XHTML file within the EPUB
            book_id: DB book UUID
        """
        current_dir = os.path.dirname(current_xhtml_path)

        def resolve_path(match):
            """Resolve relative paths and rewrite to endpoint URL."""
            attr_name = match.group(1)
            original_path = match.group(2)
            if original_path.startswith(('http://', 'https://', 'data:', '//')):
                return match.group(0)

            if current_dir and not original_path.startswith('/'):
                resolved = os.path.normpath(os.path.join(current_dir, original_path))
                resolved = resolved.replace('\\', '/')
            else:
                resolved = original_path.lstrip('/')

            new_url = (
                f"/book/epub_resource?book_id={quote(book_id)}"
                f"&amp;resource_path={quote(resolved)}"
            )

            return f'{attr_name}="{new_url}"'

        # Rewrite href and src attributes
        # Pattern captures: (href|src)=["'](path)["']
        html_content = re.sub(
            r'(href|src)=["\']((?!http://|https://|data:|//)[^"\']+)["\']',
            resolve_path,
            html_content
        )

        return html_content

    async def extract_text_from_book(self, epub_path: str) -> str:
        """
        Extract all text content from an EPUB file.
        
        Args:
            epub_path: Path to the EPUB file
            
        Returns:
            Plain text content of the book
        """
        # Read container.xml
        container_xml = await self.read_epub_file(
            epub_path=epub_path,
            internal_path='META-INF/container.xml'
        )
        container_xml = container_xml.decode('utf-8')
        
        # Get path to content.opf
        opf_path = await self.get_opf_path(container_xml)
        
        # Get ordered XHTML files (chapters)
        ordered_files = await self.get_spine_order(epub_path, opf_path)
        
        # Extract text from each chapter
        all_text = []
        for chapter_path in ordered_files:
            chapter_content = await self.read_epub_file(epub_path, chapter_path)
            chapter_str = chapter_content.decode('utf-8') if isinstance(
                chapter_content, bytes
            ) else chapter_content
            
            # Parse HTML and extract text
            soup = BeautifulSoup(chapter_str, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            all_text.append(text)
        
        return '\n\n'.join(all_text)
