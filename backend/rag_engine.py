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

# 3. DIRECT SEARCH FUNCTION (Upgraded for Resumes & Security!)
def search_similar_documents(query: str, k: int = 10, username: str = None):
    """
    Embeds query, searches DB, and strictly filters by user.
    """
    # Generate the vector for the user's question
    query_vector = embeddings.embed_query(query)
    
    params = {
        "query_embedding": query_vector,
        "match_threshold": 0.2, # Lowered from 0.5! This is critical for resumes to pass the check.
        "match_count": k # Give me 10 chunks to get the full picture
    }
    
    response = supabase.rpc("match_documents", params).execute()
    
    results = []
    for record in response.data:
        meta = record['metadata']
        
        # THE BOUNCER: Only keep the chunk if it's a public FAQ OR it belongs to this specific user.
        if meta.get("source") == "faq_system" or meta.get("user_id") == username:
            doc = Document(page_content=record['content'], metadata=meta)
            results.append((doc, record['similarity']))
            
    return results

# 4. Ingestion Function (Process & Upload)
def index_document(text: str, metadata: dict):
    print(f"📄 Processing document: {metadata.get('filename')}...")
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(text)
    
    docs = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]
    
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
    seed_initial_data()