from fastapi import Request
from typing import Union, List
from src.qa import QASystem
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
from typing import Optional
from pydantic import BaseModel
import os


class ZaniaQASchema(BaseModel):
    url: str
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


@app.get("/")
def hello():
    return "Welcome to Zania QA API"


@app.post("/answer_question")
def answer_question(body: ZaniaQASchema, request: Request):
    # Initialize and set up the QA system
    qa_system = QASystem(body.url)
    qa_system.initialize_pipeline()
    answer = qa_system.answer_question(body.query)
    return {"answer": answer}


if __name__ == '__main__':
    uvicorn.run(app, port=5001, host="0.0.0.0")