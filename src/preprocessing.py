from langchain.text_splitter import RecursiveCharacterTextSplitter

class TextSplitter:
    def __init__(self, chunk_size=1000, chunk_overlap=20):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_documents(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, 
            chunk_overlap=self.chunk_overlap
        )
        return text_splitter.split_documents(documents)
