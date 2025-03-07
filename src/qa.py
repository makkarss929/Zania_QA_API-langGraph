import os
from concurrent.futures import ThreadPoolExecutor
from typing import Union, List

import openai
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import ChatOpenAI

from src.langraph_pipeline import LangraphPipeline
from src.pdf import AbstractPDFLoader
from src.preprocessing import AbstractTextSplitter
from src.vector_db import AbstractVectorDB

_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']


class QASystem:
    def __init__(
            self,
            pdf_loader: AbstractPDFLoader,
            text_splitter: AbstractTextSplitter,
            vector_db: AbstractVectorDB,
            llm: ChatOpenAI
    ):
        self.pdf_loader = pdf_loader
        self.text_splitter = text_splitter
        self.vector_db = vector_db
        self.llm = llm
        self.pipeline = None
        self.retriever = None

    def initialize_pipeline(self):
        documents = self.pdf_loader.load_documents()
        chunked_documents = self.text_splitter.split_documents(documents)
        self.vector_db.create_database(chunked_documents)
        self.retriever = self.vector_db.get_retriever()
        # Create the LangraphPipeline instance
        self.pipeline = LangraphPipeline(self.retriever, self.llm)

    def answer_question(self, query: Union[str, List[str]]):
        if not self.pipeline:
            raise ValueError("QA pipeline has not been initialized.")

        if isinstance(query, list):
            results = []
            with ThreadPoolExecutor() as executor:
                # Use self.process_single_query for each question
                future_answers = executor.map(self.process_single_query, query)
                for question, answer in zip(query, future_answers):
                    results.append({"question": question, "answer": answer})
            return results

        elif isinstance(query, str):
            return {"question": query, "answer": self.process_single_query(query)}

    def process_single_query(self, query: str):
        """Processes a single query using the LangraphPipeline."""
        result = self.pipeline.invoke({"query": query})  # Use the invoke method
        return result.get("answer", "No answer found.")
