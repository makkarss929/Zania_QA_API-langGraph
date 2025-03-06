## Zania QA API - Langraph

* Creating a robust and scalable QA microservice


### High-Level Diagram


```mermaid
graph LR
    A[Client] --> B(FastAPI Application);
    B --> C{LangGraph Pipeline};
    C --> D[Document Retrieval];
    D --> E(ChatOpenAI);
    E --> F[Answer];
    F --> B;
    B --> A;
```

### Low - level Diagram

```mermaid
classDiagram
    class FastAPI {
        +app: Starlette
        +routes: List~APIRoute~
        +middleware: List~Middleware~
        +add_middleware(middleware: Middleware)
        +add_api_route(path: str, endpoint: Callable, ...)
    }

    class Starlette {
        +routes: List~BaseRoute~
        +middleware: List~Middleware~
        +__call__(scope: Scope, receive: Receive, send: Send)
    }

    class APIRoute {
        +path: str
        +endpoint: Callable
        +handle(scope: Scope, receive: Receive, send: Send)
    }

    class CORSMiddleware {
        +allow_origins: List~str~
        +allow_methods: List~str~
        +__call__(scope: Scope, receive: Receive, send: Send)
    }

    class ZaniaQASchema {
        +query: Union~str, List~str~~
    }

    class QASystem {
        +pdf_loader: AbstractPDFLoader
        +text_splitter: AbstractTextSplitter
        +vector_db: AbstractVectorDB
        +llm: ChatOpenAI
        +graph: StateGraph
        +retriever: VectorStoreRetriever
        +initialize_pipeline()
        +answer_question(query: Union~str, List~str~~)
    }

    class AbstractPDFLoader {
        <<Interface>>
        +load_documents() List~Document~
    }

    class PDFLoader {
        +path: str
        +load_documents() List~Document~
    }

    class AbstractTextSplitter {
        <<Interface>>
        +split_documents(documents: List~Document~) List~Document~
    }

    class TextSplitter {
        +chunk_size: int
        +chunk_overlap: int
        +split_documents(documents: List~Document~) List~Document~
    }

    class AbstractVectorDB {
        <<Interface>>
        +create_database(documents: List~Document~)
        +get_retriever(k: int) VectorStoreRetriever
    }

    class VectorDB {
        +embeddings: OpenAIEmbeddings
        +db: DocArrayInMemorySearch
        +create_database(documents: List~Document~)
        +get_retriever(k: int) VectorStoreRetriever
    }

   class DocArrayInMemorySearchRetriever {
        +search_kwargs: Dict~str, int~
        +get_relevant_documents(query: str) List~Document~
    }

    class ChatOpenAI {
        +client: OpenAI
        +model_name: str
        +temperature: float
        +invoke(prompt: PromptValue) str
    }

    class OpenAI {
       +api_key: str
       + ChatCompletion.create(...)
    }

    class PromptValue {
        <<Interface>>
        +to_messages() List~BaseMessage~
    }

    class StateGraph {
        +add_node(name: str, func: Callable)
        +add_edge(start: str, end: str)
        +set_entry_point(node_name: str)
        +compile()
        +invoke(input: Dict)
    }

    class GraphState {
        +query: str
        +documents: List~Document~
        +answer: Optional~str~
        +retriever: DocArrayInMemorySearchRetriever
        +llm: ChatOpenAI
    }

    class Document {
        +metadata: Dict~str, Any~
        +page_content: str
    }

    FastAPI "1" -- "1" Starlette : Contains
    FastAPI "1" -- "*" APIRoute : Uses
    FastAPI "1" -- "*" CORSMiddleware : Uses
    APIRoute "1" -- "1" ZaniaQASchema : Receives Data
    APIRoute "1" -- "1" QASystem : Uses
    QASystem "1" -- "1" AbstractPDFLoader : Uses
    QASystem "1" -- "1" AbstractTextSplitter : Uses
    QASystem "1" -- "1" AbstractVectorDB : Uses
    QASystem "1" -- "1" ChatOpenAI : Uses
    QASystem "1" -- "1" StateGraph : Uses
    QASystem "1" -- "1" DocArrayInMemorySearchRetriever : Uses
    PDFLoader --|> AbstractPDFLoader : Implements
    TextSplitter --|> AbstractTextSplitter : Implements
    VectorDB --|> AbstractVectorDB : Implements
    GraphState "1" -- "0..*" Document : Contains
    ChatOpenAI ..> OpenAI: Uses
    ChatOpenAI ..> PromptValue : Receives Prompt
```

```mermaid
graph LR
    subgraph QASystem
    A[Start: retrieve] --> B(retrieve Node);
    B --> C(generate Node);
    C --> D[End];
    end

    style A fill:#003366,stroke:#333,stroke-width:2px,color:#FFFFFF
    style D fill:#003366,stroke:#333,stroke-width:2px,color:#FFFFFF
```


## Code Architecture

* In Code Architecture, we are following `OOPS` and `SOLID5` principles to make code more efficient `modular, flexible, extensible, scalable`.
* Usually `open source repos` follow this [principles](https://realpython.com/solid-principles-python/), `SRP` and `DIP` are widely used.
* Coding steps
  1. Loading `PDF` -> Creating `PDFLoader` class, following `SRP (Single Responsibility Principle)`
  2. Converting documents into `small chunks`, -> Creating `TextSplitter` class for that. following `SRP (Single Responsibility Principle)`
  3. Creating `In Memory vector DB`. --> Creating `VectorDB` class for that, following `SRP (Single Responsibility Principle)`
  4. finally, creating `QASystem` Class, and following `Facade Pattern, DIP (Dependency Inversion Principle)`, and `integrating 3 previous classes` and creating `answer_question function` in QASystem as single entry point.

* Using `ThreadPoolExecutor` for concurrent processing for making parallel calls, getting results faster.



## System Architecture

* Using `FastAPI` as backend, which is `reliable` and `robust`.
* After that doing `containerization` with `Docker`, which is further easy to scale.
* If we want to scale we can add `Load balancers` by adding `nginx` container, we can easily create `replicas`, by transforming it into `Multi Container Architecture` using `Docker compose`. 


## Input Schema for route `/` - POST request


```
{
  "query": ["What is the name of the company?",
    "Who is the CEO of the company?",
    "What is their vacation policy?",
    "What is the termination policy?",
    "Please provide an Overview of OOPs principles?"]

}
```
## Output Schema


```
{
  "answer": [
    {
      "question": "What is the name of the company?",
      "answer": "The name of the company is Zania, Inc."
    },
    {
      "question": "Who is the CEO of the company?",
      "answer": "The CEO of the company is Shruti Gupta."
    },
    {
      "question": "What is their vacation policy?",
      "answer": "The company generally grants requests for vacation when possible, taking business needs into consideration. When multiple employees request the same time off, their length of employment, seniority, or collective-bargaining agreement may determine priority in scheduling vacation times. Employees must take vacation in increments of at least a specified number of hours or days. \n\nDuring a leave of absence, the company may require employees to use any unused vacation during disability or family medical leave, or any other leave of absence, where permissible under local, state, and federal law. \n\nUnused vacation can typically be carried over to the following year, but specific conditions for carryover may apply. Employees will accrue vacation based on a specified amount for every period of time worked, up to a maximum accrual amount. Once the maximum accrual is reached, no additional vacation will accrue until some of the accrued but unused vacation is used.\n\nEmployees are encouraged to use their vacation time and are eligible to begin using it immediately upon hire or after a specified introductory period. Requests for vacation should be made to the manager as far in advance as possible, but at least a specified number of days or weeks in advance."
    },
    {
      "question": "What is the termination policy?",
      "answer": "The termination policy states that employment is on an \"at-will\" basis, meaning that either the employee or the company can terminate the employment relationship at any time. In appropriate circumstances, management may provide a verbal warning followed by written warnings, and if the conduct does not improve, it may lead to demotion, transfer, forced leave, or termination. However, the company is not obligated to follow any specific disciplinary or grievance procedure and may discipline or terminate employees without prior warning or procedure, depending on the circumstances. Violations of company policies may result in disciplinary action, including immediate termination."
    },
    {
      "question": "Please provide an Overview of OOPs principles?",
      "answer": "I don't know."
    }
  ]
}
```

## Deployment Instructions

1. clone the `repo`.
2. Place `.env` in root of folder.
3. Place `handbook.pdf` in `fixtures` folder.

### Execute API using Docker

```bash
docker build -t zania_qa_api .
docker run -p 5001:5001 -m 1G zania_qa_api
```

### Execute API using virtual environments


```bash
cd Zania_QA_API/
python3 -m venv venv
# Linux
source venv/bin/activate
# windows
.\venv\Scripts\activate.bat

pip install --no-cache-dir -r requirements.txt

python app.py
```

## CURL Request

```bash

curl -X 'POST' \
  'http://0.0.0.0:5001/answer_question' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": ["What is the name of the company?",
"Who is the CEO of the company?",
"What is their vacation policy?",
"What is the termination policy?",
"Please provide an Overview of OOPs principles?"]}'
```