from langchain.document_loaders import PyPDFLoader

# PDFLoader Class (Single Responsibility Principle)
class PDFLoader:
    def __init__(self, path: str):
        self.path = path

    def load_documents(self):
        loader = PyPDFLoader(self.path)
        pages = loader.load_and_split()
        return pages
