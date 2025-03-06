from abc import ABC, abstractmethod

from langchain.document_loaders import PyPDFLoader


class AbstractPDFLoader(ABC):
    @abstractmethod
    def load_documents(self):
        pass


# PDFLoader Class (Single Responsibility Principle)
class PDFLoader(AbstractPDFLoader):
    def __init__(self, path: str):
        self.path = path

    def load_documents(self):
        loader = PyPDFLoader(self.path)
        pages = loader.load_and_split()
        return pages
