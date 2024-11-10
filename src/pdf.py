import os
import requests
import tempfile
from langchain.document_loaders import PyPDFLoader


# Single Responsibility Principle (SRP): PDFDownloader class handles downloading and cleanup
class PDFDownloader:
    def __init__(self, url: str):
        self.url = url
        self._temp_pdf_path = None

    def download_pdf(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            response = requests.get(self.url)
            response.raise_for_status()
            temp_pdf.write(response.content)
            self._temp_pdf_path = temp_pdf.name
            return self._temp_pdf_path


    def cleanup(self):
        if self._temp_pdf_path and os.path.exists(self._temp_pdf_path):
            os.remove(self._temp_pdf_path)
            print(f"Temporary file {self._temp_pdf_path} deleted.")
            self._temp_pdf_path = None



# PDFLoader Class (Single Responsibility Principle)
class PDFLoader:
    def __init__(self, path: str):
        self.path = path

    def load_documents(self):
        loader = PyPDFLoader(self.path)
        pages = loader.load_and_split()
        return pages
