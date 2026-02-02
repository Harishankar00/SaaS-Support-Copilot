import os
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

# We still use this, but we'll force it to be lightweight
# If this still fails, we will switch to the API method.
try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
except Exception:
    # Fallback if local install is totally broken
    from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key=os.getenv("HF_TOKEN"), 
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

DB_PATH = "vector_db/faiss_index"

def create_vector_db():
    if not os.path.exists("data/faq.json"):
        print("Error: data/faq.json not found!")
        return

    with open("data/faq.json", "r") as f:
        data = json.load(f)
    
    documents = [
        Document(
            page_content=f"Question: {item['question']}\nAnswer: {item['answer']}",
            metadata=item
        ) for item in data
    ]
    
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(DB_PATH)
    print("✅ FAISS Vector DB created successfully.")

def get_retriever():
    # allow_dangerous_deserialization is required for loading local FAISS files
    vector_store = FAISS.load_local(
        DB_PATH, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    return vector_store.as_retriever(search_kwargs={"k": 3})

if __name__ == "__main__":
    create_vector_db()