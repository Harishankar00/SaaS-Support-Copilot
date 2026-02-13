import os
import json
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

# NEW: Import the modern embedding classes
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings

load_dotenv()

DB_PATH = "vector_db/faiss_index"

def get_embeddings():
    """
    Factory function to get the best available embedding model.
    Prioritizes Local (fast/free) -> Falls back to API (serverless).
    """
    try:
        # Option 1: Run Locally (Best for stability)
        # This downloads the small model (~80MB) to your machine once.
        print("🔌 Attempting to load local embeddings (all-MiniLM-L6-v2)...")
        return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        print(f"⚠️ Local load failed: {e}")
        print("☁️ Switching to Hugging Face API (Serverless)...")
        
        # Option 2: Use the Modern API Class
        # This fixes the 'KeyError: 0' by correctly parsing API responses
        return HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=os.getenv("HF_TOKEN")
        )

# Initialize embeddings once to be used globally
embeddings = get_embeddings()

def create_vector_db():
    if not os.path.exists("data/faq.json"):
        print("❌ Error: data/faq.json not found!")
        return

    print("📊 Loading data from faq.json...")
    with open("data/faq.json", "r") as f:
        data = json.load(f)
    
    documents = [
        Document(
            page_content=f"Question: {item['question']}\nAnswer: {item['answer']}",
            metadata={"question": item['question'], "answer": item['answer']}
        ) for item in data
    ]
    
    if not documents:
        print("⚠️ No documents found to index!")
        return

    print(f"🚀 Creating Vector DB with {len(documents)} documents...")
    # This might take a moment if using the API
    vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(DB_PATH)
    print(f"✅ FAISS Vector DB successfully saved to {DB_PATH}")

def get_retriever():
    """
    Loads the Vector DB and returns a retriever interface.
    """
    if not os.path.exists(DB_PATH):
        print("⚠️ Vector DB not found. Creating it now...")
        create_vector_db()

    # We must use the exact same 'embeddings' object that created the DB
    vector_store = FAISS.load_local(
        DB_PATH, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    return vector_store

if __name__ == "__main__":
    # If run directly, just rebuild the DB
    create_vector_db()