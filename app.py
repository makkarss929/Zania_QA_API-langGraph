import os
from typing import Union, List

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import ChatOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv


# Import implementations
from src.pdf import PDFLoader
from src.preprocessing import TextSplitter
from src.qa import QASystem
from src.vector_db import VectorDB

load_dotenv(find_dotenv())

class ZaniaQASchema(BaseModel):
    query: Union[str, List[str]]


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize and set up the QA system
# Ensure handbook.pdf is present in the fixtures folder during Docker build
pdf_loader = PDFLoader(os.path.join("fixtures", "handbook.pdf"))
text_splitter = TextSplitter()
vector_db = VectorDB()
llm = ChatOpenAI(temperature=0.0, model="gpt-4o")  # or any other suitable model

qa_system = QASystem(pdf_loader, text_splitter, vector_db, llm)
qa_system.initialize_pipeline()


@app.get("/")
def hello():
    return "Welcome to Zania QA API"


@app.post("/answer_question")
async def answer_question(body: ZaniaQASchema, request: Request):
    result = await qa_system.answer_question(body.query)
    return result


if __name__ == '__main__':
    uvicorn.run(app, port=5001, host="0.0.0.0")