import os
import json
from dotenv import load_dotenv
from supabase.client import create_client, Client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

load_dotenv()

# 1. Setup Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. Setup Embeddings
print("🔌 Loading embedding model (all-MiniLM-L6-v2)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. DIRECT SEARCH FUNCTION (The Critical Fix)
def search_similar_documents(query: str, k: int = 4):
    """
    Embeds the query and calls the 'match_documents' RPC function directly.
    Bypasses the LangChain wrapper to avoid version mismatch errors.
    """
    # 1. Generate the vector for the user's question
    query_embedding = embeddings.embed_query(query)
    
    # 2. Call the SQL function we created in Supabase
    params = {
        "query_embedding": query_embedding,
        "match_threshold": 0.5, # Only return relevant chunks
        "match_count": k
    }
    
    # 3. Execute RPC
    response = supabase.rpc("match_documents", params).execute()
    
    # 4. Convert results to the format main.py expects
    results = []
    for record in response.data:
        doc = Document(
            page_content=record['content'],
            metadata=record['metadata']
        )
        # Append tuple: (Document object, similarity score)
        results.append((doc, record['similarity']))
        
    return results

# 4. Ingestion Function (Process & Upload)
def index_document(text: str, metadata: dict):
    """
    Takes raw text, splits it, and saves it to Supabase.
    """
    print(f"📄 Processing document: {metadata.get('filename')}...")
    
    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    
    # Prepare documents
    docs = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]
    
    # Use LangChain wrapper for INSERTING (Writing works fine, only Reading was buggy)
    vector_store = SupabaseVectorStore(
        client=supabase, 
        embedding=embeddings, 
        table_name="documents",
        query_name="match_documents"
    )
    vector_store.add_documents(docs)
    
    print(f"✅ Successfully indexed {len(docs)} chunks to Supabase!")
    return len(docs)

# 5. Migration Helper
def seed_initial_data():
    """
    Reads faq.json and uploads it to Cloud.
    """
    if not os.path.exists("data/faq.json"):
        return

    print("🌱 Seeding initial FAQ data to Supabase...")
    with open("data/faq.json", "r") as f:
        data = json.load(f)
    
    docs = []
    for item in data:
        content = f"Question: {item['question']}\nAnswer: {item['answer']}"
        meta = {"source": "faq_system", "type": "official"}
        docs.append(Document(page_content=content, metadata=meta))
    
    vector_store = SupabaseVectorStore(
        client=supabase, 
        embedding=embeddings, 
        table_name="documents",
        query_name="match_documents"
    )
    vector_store.add_documents(docs)
    print("✅ FAQ data seeded to Cloud!")

if __name__ == "__main__":
    # If run directly, try to seed data
    seed_initial_data()