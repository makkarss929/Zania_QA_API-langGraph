from fastapi import Request
from bin.helper import ZaniaQA
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
from typing import Optional
from pydantic import BaseModel
import os


class ZaniaQASchema(BaseModel):
    query: str


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

obj = ZaniaQA()
obj.pipeline(os.path.join("fixtures", "handbook.pdf"))

@app.get("/")
def hello():
    return "Welcome to Zania QA API"


@app.post("/")
def handler(body: ZaniaQASchema, request: Request):
    answer = obj.inference(body.query)
    return {"answer": answer}


if __name__ == '__main__':
    uvicorn.run(app, port=5001, host="0.0.0.0")