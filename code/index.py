from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
import json

embedding = OpenAIEmbeddings(openai_api_key="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")
docs = []
with open("australia_spatial_corpus.jsonl", "r") as f:
    for line in f:
        item = json.loads(line)
        docs.append(Document(page_content=item["text"], metadata={"type": item["type"]}))

vectorstore = FAISS.from_documents(docs, embedding)
vectorstore.save_local("australia_spatial_index")
