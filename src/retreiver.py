from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from sklearn.metrics.pairwise import cosine_similarity
from langchain.schema import HumanMessage, SystemMessage



class CustomRetrievalQAPipeline:
    def __init__(self, model_name, vector_db, top_k=5, threshold=0.5):
        self.llm = ChatOpenAI(temperature=0.0, model=model_name)
        self.vector_db = vector_db
        self.top_k = top_k        # Number of top documents to retrieve
        self.threshold = threshold # Minimum relevance score threshold


    def retrieve_documents(self, query):
        # Step 1: Embed the query
        query_embedding = self.vector_db.embeddings.embed_query(query)
        # Step 2: Retrieve all documents and their embeddings
        docs = self.vector_db.db.similarity_search_by_vector(query_embedding, k=self.top_k, score_threshold=self.threshold)
        return docs

    def generate_answer(self, documents, query):
        # Concatenate documents for the LLM context
        context = "\n".join([doc.page_content for doc in documents])
        
        # Create system and human messages
        system_message = SystemMessage(content=(
            "You are a QA assistant. Given the following context and query, provide a concise answer. "
            "If context is not available or query is not related to context, then say I don't know."
        ))
        
        human_message = HumanMessage(content=(
            f"Context:\n{context}\n\n"
            f"Query: {query}\n\n"
            f"Answer:"
        ))
        
        # Generate an answer from the LLM using proper message format
        messages = [system_message, human_message]
        response = self.llm(messages)
        
        return response.content

    def run(self, query):
        # Step 1: Retrieve top K documents above the relevance threshold
        documents = self.retrieve_documents(query)

        # Step 2: Generate answer based on retrieved documents
        answer = self.generate_answer(documents, query)
        
        # Optionally, return both the answer and the scores for transparency
        return answer
