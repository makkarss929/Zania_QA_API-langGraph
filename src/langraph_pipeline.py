from typing import TypedDict, List, Optional, Dict

from langchain.chat_models import ChatOpenAI
from langchain.docstore.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain_core.vectorstores import VectorStoreRetriever
from langgraph.graph import StateGraph, END


class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    query: str
    documents: List[Document]
    answer: Optional[str]
    retriever: VectorStoreRetriever
    llm: ChatOpenAI


class LangraphPipeline:
    def __init__(self, retriever: VectorStoreRetriever, llm: ChatOpenAI):
        self.retriever = retriever
        self.llm = llm
        self.graph = self.build_graph()

    def build_graph(self):
        """Builds the LangGraph pipeline."""

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
            docs = state['documents']
            llm = state['llm']
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

        builder = StateGraph(GraphState)
        builder.add_node("retrieve", retrieve)
        builder.add_node("generate", generate)
        builder.set_entry_point("retrieve")
        builder.add_edge("retrieve", "generate")
        builder.add_edge("generate", END)

        return builder.compile()

    def invoke(self, input_data: Dict) -> Dict:
        """Invokes the LangGraph pipeline."""

        # Ensure the input data is in the correct format for GraphState
        input_for_graph = {
            "query": input_data["query"],
            "documents": [],  # Start with an empty list of documents
            "answer": None,  # Start with no answer
            "retriever": self.retriever,  # Pass the retriever
            "llm": self.llm  # Pass the LLM
        }
        return self.graph.invoke(input_for_graph)
