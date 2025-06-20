from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import json

embedding = OpenAIEmbeddings(openai_api_key="your-key")
docs = []
with open("australia_spatial_corpus.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        docs.append(Document(page_content=item["text"], metadata={"type": item["type"]}))

vectorstore = FAISS.from_documents(docs, embedding)
vectorstore.save_local("australia_spatial_index")
