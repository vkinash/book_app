import ebooklib

from fastapi import APIRouter, UploadFile
from ebooklib import epub
from api.services.epub import EPUBData
from bs4 import BeautifulSoup as soup



router = APIRouter(
    prefix="/book",
    tags=["books"]
)


@router.post("/epub_book/")
async def get_epub_book_data(file_name: UploadFile):
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

    book = EPUBData(file_name=f"books_test/{file_name.filename}")
    images = book.list_of_images()
    docs = book.list_of_documents()
    unknown = book.list_of_unknown()
    content = list([(str(doc), soup(book.get_documents_content(doc), "xml").get_text()) for doc in docs])

    return {"docs": content, "images": str(images)}
