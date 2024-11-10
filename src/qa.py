import os
import openai
from typing import Union, List
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from src.pdf import PDFLoader
from src.vector_db import VectorDB
from src.preprocessing import TextSplitter
# Use ThreadPoolExecutor for concurrent processing
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

# QASystem Class (Facade Pattern, Dependency Inversion Principle)
class QASystem:
    def __init__(self, path: str):
        self.path = path
        self.loader = PDFLoader(path)
        self.splitter = TextSplitter()
        self.vector_db = VectorDB()
        self.model_selector = "gpt-4o-mini"
        self.qa_pipeline = None

    def initialize_pipeline(self):
        # Load and split PDF into chunks
        documents = self.loader.load_documents()
        chunked_documents = self.splitter.split_documents(documents)
        
        # Create vector database
        self.vector_db.create_database(chunked_documents)
        retriever = self.vector_db.get_retriever()
        
        # Set up language model and QA chain
        model_name = self.model_selector.get_model_name()
        llm = ChatOpenAI(temperature=0.0, model=model_name)
        self.qa_pipeline = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff", 
            retriever=retriever,
            verbose=True
        )

    def answer_question(self, query: Union[str, List[str]]):
        if not self.qa_pipeline:
            raise ValueError("QA pipeline has not been initialized.")
        
        if isinstance(query, list):
            answers = []
            with ThreadPoolExecutor() as executor:
                # Map questions to concurrent execution
                future_answers = executor.map(self.qa_pipeline.run, query)
                # Collect results
                for question, answer in zip(query, future_answers):
                    answers.append({"question": question, "answer": answer})
            return answers
        
        elif isinstance(query, str):
            answer = self.qa_pipeline.run(query)
            return {"question": query, "answer": answer}

        
        
