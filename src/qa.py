import os
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict
from typing import Union, List, Dict, Optional

import openai
from dotenv import load_dotenv, find_dotenv
from langchain.chains.summarize import load_summarize_chain
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
    summaries: List[str]  # Add summaries to the state
    pdf_loader: AbstractPDFLoader
    text_splitter: AbstractTextSplitter
    vector_db: AbstractVectorDB


# Node Functions

def load_documents(state: GraphState) -> Dict[str, List[Document]]:
    """Loads PDF documents."""
    print("Entering load_documents node")
    pdf_loader = state['pdf_loader']
    documents = pdf_loader.load_documents()
    return {"documents": documents}


def summarize_documents(state: GraphState) -> Dict[str, List[str]]:
    """Summarizes PDF documents."""
    print("Entering summarize_documents node")
    documents = state['documents']
    llm = state['llm']
    summaries = []
    for doc in documents:
        chain = load_summarize_chain(llm, chain_type="stuff")
        summary = chain.run([doc])
        summaries.append(summary)
    return {"summaries": summaries}


def create_vector_db(state: GraphState) -> Dict[str, VectorStoreRetriever]:
    """Creates vector database."""
    print("Entering create_vector_db node")
    text_splitter = state['text_splitter']
    vector_db = state['vector_db']
    documents = state['documents']
    chunked_documents = text_splitter.split_documents(documents)
    vector_db.create_database(chunked_documents)
    retriever = vector_db.get_retriever()
    return {"retriever": retriever}


def retrieve(state: GraphState) -> Dict[str, List[Document]]:
    """Fetches relevant documents based on the query."""
    print("Entering retrieve node")
    query = state['query']
    retriever = state['retriever']
    docs = retriever.get_relevant_documents(query)
    print(f"Retrieved {len(docs)} documents")
    return {"documents": docs}


def rerank(state: GraphState) -> Dict[str, List[Document]]:
    """Reranks the retrieved documents."""
    print("Entering rerank node")
    # This is a placeholder for the reranking logic.  You would need to
    # integrate a reranking model (e.g., using Hugging Face Transformers).
    # For now, it simply returns the original documents.
    documents = state['documents']
    print("No Reranking Model so defaulting to original Model.")
    return {"documents": documents}


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
        # Build LangGraph
        self.build_graph()

    def build_graph(self):
        builder = StateGraph(GraphState)

        builder.add_node("load_documents", load_documents)
        builder.add_node("summarize_documents", summarize_documents)
        builder.add_node("create_vector_db", create_vector_db)
        builder.add_node("retrieve", retrieve)
        builder.add_node("rerank", rerank)
        builder.add_node("generate", generate)

        builder.set_entry_point("load_documents")
        builder.add_edge("load_documents", "summarize_documents")
        builder.add_edge("summarize_documents", "create_vector_db")
        builder.add_edge("create_vector_db", "retrieve")
        builder.add_edge("retrieve", "rerank")
        builder.add_edge("rerank", "generate")
        builder.add_edge("generate", END)  # graph must end

        self.graph = builder.compile()

    def answer_question(self, query: Union[str, List[str]]):
        if not self.graph:
            raise ValueError("QA graph has not been initialized.")

        if isinstance(query, list):
            answers = []
            with ThreadPoolExecutor() as executor:
                # Map questions to concurrent execution
                future_answers = executor.map(self.process_single_query, query)
                # Collect results
                for question, answer in zip(query, future_answers):
                    answers.append({"question": question, "answer": answer})
            return answers

        elif isinstance(query, str):
            return self.process_single_query(query)

    def process_single_query(self, query: str):
        """Processes a single query using the LangGraph."""

        inputs = {"query": query, "documents": [], "answer": None, "retriever": self.retriever, "llm": self.llm,
                  'text_splitter': self.text_splitter,
                  'pdf_loader': self.pdf_loader, 'vector_db': self.vector_db, 'summaries': []}
        result = self.graph.invoke(inputs)
        return {"question": query, "answer": result.get("answer", "No answer found.")}
