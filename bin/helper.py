import openai
import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

embeddings = OpenAIEmbeddings()

# account for deprecation of LLM model
import datetime
# Get the current date
current_date = datetime.datetime.now().date()
# Define the date after which the model should be set to "gpt-3.5-turbo"
target_date = datetime.date(2024, 6, 12)
# Set the model variable based on the current date
if current_date > target_date:
    llm_model = "gpt-3.5-turbo"
else:
    llm_model = "gpt-3.5-turbo-0301"


class ZaniaQA:
    
    def loading_pdf(self, path):
        loader = PyPDFLoader(path)
        pages = loader.load_and_split()
        # as pdf is large coverting that into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=20)
        chunk_docs = text_splitter.split_documents(pages)
        return chunk_docs

    def creating_vector_db(self, chunk_docs):
        db = DocArrayInMemorySearch.from_documents(
            chunk_docs, 
            embeddings
        )
        
        return db
        

    def creating_retreiver(self, db):
        retriever = db.as_retriever(search_kwargs={"k": 3})
        llm = ChatOpenAI(temperature = 0.0, model=llm_model)
        qa_stuff = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff", 
            retriever=retriever, 
            verbose=True
        )
        return qa_stuff

    def pipeline(self, path):
        chunk_docs = self.loading_pdf(path)
        db = self.creating_vector_db(chunk_docs)
        qa_stuff = self.creating_retreiver(db)
        self.qa_stuff = qa_stuff

        
    def inference(self, query):
        response = self.qa_stuff.run(query)
        return response
    