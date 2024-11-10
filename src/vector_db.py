import os
import openai
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']
print("os.environ['OPENAI_API_KEY']", os.environ['OPENAI_API_KEY'])

class VectorDB:
    def __init__(self, embedding_model=None):
        self.embeddings = embedding_model or OpenAIEmbeddings()
        self.db = None

    def create_database(self, documents):
        self.db = DocArrayInMemorySearch.from_documents(documents, self.embeddings)

    def get_retriever(self, k=3):
        if not self.db:
            raise ValueError("Database has not been initialized.")
        return self.db.as_retriever(search_kwargs={"k": k})
