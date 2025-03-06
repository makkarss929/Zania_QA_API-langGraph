import os
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict
from typing import Union, List, Dict, Optional

import openai
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever
# LangGraph imports
from langgraph.graph import StateGraph, END

# Abstract data loaders and splitters
from src.pdf import AbstractPDFLoader
from src.preprocessing import AbstractTextSplitter
from src.vector_db import AbstractVectorDB

_ = load_dotenv(find_dotenv())
openai.api_key = os.environ['OPENAI_API_KEY']


class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        query: The user question.
        documents: Retrieved documents.
        answer: The final answer.
    """
    query: str
    documents: List[Document]
    answer: Optional[str]  # Make it optional to start with
    retriever: VectorStoreRetriever
    llm: ChatOpenAI


# Node Functions

def retrieve(state: GraphState) -> Dict[str, List[Document]]:
    """Fetches relevant documents based on the query."""
    print("Entering retrieve node")
    query = state['query']
    retriever = state['retriever']
    docs = retriever.get_relevant_documents(query)
    print(f"Retrieved {len(docs)} documents")
    return {"documents": docs}


def generate(state: GraphState) -> Dict[str, str]:
    """Generates an answer based on the retrieved documents and query."""
    print("Entering generate node")
    query = state['query']
    docs = state['documents']  # Access documents from the state
    llm = state['llm']  # Access llm from the state
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant that answers questions based on the provided context.
        If the context does not contain the answer to the question, or if the context is not relevant to the question,
        simply respond with: 'I am sorry, but the provided context does not contain the answer to the question.'\n\nContext:\n{context}"""),
        ("human", "{question}")
    ])
    chain = (
            {"context": lambda x: "\n".join([doc for doc in x]), "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )
    answer = chain.invoke(
        {"context": docs, "question": query}
    )

    print(f"Generated answer: {answer}")
    return {"answer": answer}


# QASystem Class (Facade Pattern, Dependency Inversion Principle)
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
        self.graph = None  # LangGraph
        self.retriever = None

    def initialize_pipeline(self):
        # Load and split PDF into chunks
        documents = self.pdf_loader.load_documents()
        chunked_documents = self.text_splitter.split_documents(documents)

        # Create vector database
        self.vector_db.create_database(chunked_documents)
        self.retriever = self.vector_db.get_retriever()
        # Build LangGraph
        self.build_graph()

    def build_graph(self):
        builder = StateGraph(GraphState)

        builder.add_node("retrieve", retrieve)
        builder.add_node("generate", generate)

        builder.set_entry_point("retrieve")
        builder.add_edge("retrieve", "generate")
        builder.add_edge("generate", END)  # graph must end

        self.graph = builder.compile()

    def answer_question(self, query: Union[str, List[str]]):
        if not self.graph:
            raise ValueError("QA graph has not been initialized.")

        if isinstance(query, list):
            results = []
            with ThreadPoolExecutor() as executor:
                # Map questions to concurrent execution
                future_answers = executor.map(self.process_single_query, query)
                # Collect results
                for question, answer in zip(query, future_answers):
                    results.append({"question": question, "answer": answer})
            return results

        elif isinstance(query, str):
            return {"question": query, "answer": self.process_single_query(query)}

    def process_single_query(self, query: str):
        """Processes a single query using the LangGraph."""

        inputs = {"query": query, "documents": [], "answer": None, "retriever": self.retriever, "llm": self.llm}
        result = self.graph.invoke(inputs)
        return result.get("answer", "No answer found.")
