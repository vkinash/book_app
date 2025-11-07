import os
import zipfile
import re

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

    async def upload_book(self, file: UploadFile) -> str:
        """
        Upload book into books_stored directory
        :param file: file as UploadFile obj
        :return: path to file ib books_storage
        """
        saved_path = os.path.join(self.books_storage, file.filename)

        with open(saved_path, 'wb') as dst:
            while chunk := await file.read(settings.chunk_size):
                dst.write(chunk)

        return saved_path

    def get_books(self) -> list:
        """
        Get list of files in the books_stored directory
        :return: list of files
        """
        books = [
            {
                "filename": f,
                "size": os.path.getsize(os.path.join(self.books_storage, f)),
                "path": os.path.join(self.books_storage, f)
            }
            for f in os.listdir(self.books_storage)
            if f.endswith('.epub')
        ]
        return books

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

    @staticmethod
    async def read_epub_file(epub_path: str, internal_path: str) -> str:
        with zipfile.ZipFile(epub_path, 'r') as z:
            if internal_path not in z.namelist():
                raise FileNotFoundError(f"{internal_path} not found in EPUB")
            return z.read(internal_path)

    @staticmethod
    async def rewrite_resource_urls(html_content: str, file_path: str, current_xhtml_path: str) -> str:
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
            new_url = f"/book/epub_resource?file_path={quote(file_path)}&amp;resource_path={quote(resolved)}"

            return f'{attr_name}="{new_url}"'

        # Rewrite href and src attributes
        # Pattern captures: (href|src)=["'](path)["']
        html_content = re.sub(
            r'(href|src)=["\']((?!http://|https://|data:|//)[^"\']+)["\']',
            resolve_path,
            html_content
        )

        return html_content
