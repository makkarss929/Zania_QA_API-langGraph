## Zania QA API

* Created QA model based on `handbook.pdf`

## Architecture

1. Loading `PDF``
2. Converting that into `small chunks`, as LLM can process small text (1000 characters) at at time.
3. Creating `In Memory vector DB`, as I don't have access to `external vector DB`.
4. Creating `Retriever object` to retriever answers.


## Input Schema for route `/` - POST request


```
{
    "query": ""
}
```
## Output Schema


```
{
    "answer": ""
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