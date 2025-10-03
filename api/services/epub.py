import os
import ebooklib

from ebooklib import epub


class EPUBData:
    """
        The class parses data from files in EPUB format using
        ebooklib library (https://docs.sourcefabric.org/projects/ebooklib/en/latest/tutorial.html#introduction).

        Attributes:
            file_name (str): path to the file with a book in epub format.
    """
    def __init__(self, file_name):
        # Reading epub file
        self.book = epub.read_epub(file_name)

    def list_of_images(self):
        """
        The method is returning list of images objects from EPUB file
        """
        images = list()
        for img in self.book.get_items_of_type(ebooklib.ITEM_IMAGE):
            images.append(img)
            print("ITEM_IMAGE", img)
        return images

    def list_of_documents(self):
        """
        The method is returning list of documents (e.g. xhtml, xml) objects from EPUB file
        """
        docs = list()
        for doc in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            # content = doc.content.decode("utf-8")
            docs.append(doc)
            print("ITEM_DOCUMENT", doc)

        return docs

    def list_of_unknown(self):
        """
        The method is returning list of unknown objects from EPUB file
        """
        unknown_docs = list()
        for unknown in self.book.get_items_of_type(ebooklib.ITEM_UNKNOWN):
            # content = doc.content.decode("utf-8")
            unknown_docs.append(unknown)
            print("ITEM_UNKNOWN", unknown)

        return unknown_docs

    def get_documents_content(self, doc):
        return doc.get_content()
