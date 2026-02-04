import os, sqlite3
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_engine import get_retriever
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
app = FastAPI(title="SaaS Support Copilot Pro")

# Enable CORS for Next.js communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "copilot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Users Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, 
        password TEXT NOT NULL, 
        email TEXT)''')
    # Chat History Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, 
        role TEXT NOT NULL, 
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    
    # Pre-seed for easy testing
    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                       ("hari", "password123", "hari@test.com"))
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()

init_db()

client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

# --- Data Models ---
class ChatRequest(BaseModel):
    query: str
    username: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    status: str

class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# --- Persistence Helpers ---
def save_message(username, role, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (username, role, content) VALUES (?, ?, ?)", (username, role, content))
    conn.commit()
    conn.close()

# --- Auth Endpoints (Restored) ---

@app.post("/signup")
async def signup(user: UserAuth):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                       (user.username, user.password, user.email))
        conn.commit()
        return {"status": "success", "message": "User registered"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/login")
async def login(credentials: UserAuth):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE username = ? AND password = ?", 
                   (credentials.username, credentials.password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {"status": "success", "username": user[0], "token": "fake-jwt-token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- Chat & History Endpoints ---

@app.get("/history/{username}")
async def get_history(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history WHERE username = ? ORDER BY timestamp ASC", (username,))
    history = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()
    return history

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Save the user's question to the DB immediately
    save_message(request.username, "user", request.query)
    
    # 1. Greeting Handler (Hallucination-free)
    greetings = ["hi", "hello", "hey", "good morning", "wasup", "namaste"]
    if request.query.lower().strip() in greetings:
        msg = f"Hello {request.username}! I'm your NeuroStack Copilot. How can I assist you today?"
        save_message(request.username, "assistant", msg)
        return {"answer": msg, "sources": [], "status": "greeting"}

    try:
        # 2. Similarity Search with Scores
        vector_db = get_retriever().vectorstore
        docs_and_scores = vector_db.similarity_search_with_score(request.query, k=3)
        
        # 3. Minimum Relevance Threshold (Check Distance)
        # Distance < 1.1 is usually a good match in FAISS
        valid_results = [res for res in docs_and_scores if res[1] < 1.1]

        if not valid_results:
            msg = "I'm sorry, I couldn't find any documentation related to that. Please contact support."
            save_message(request.username, "assistant", msg)
            return {"answer": msg, "sources": [], "status": "no_context"}

        # 4. Build Context and call LLM
        context = "\n\n".join([d[0].page_content for d in valid_results])
        chat_completion = client.chat_completion(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": "You are a SaaS Support Assistant. Use ONLY the context provided. If not there, say you don't know."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {request.query}"}
            ],
            max_tokens=512,
            temperature=0.1
        )
        answer = chat_completion.choices[0].message.content
        
        # Save AI response to DB
        save_message(request.username, "assistant", answer)

        # Format sources with confidence percentage for the UI
        sources = []
        for doc, score in valid_results:
            confidence = max(0, 100 - int(score * 50))
            sources.append({"question": doc.metadata.get("question"), "score": f"{confidence}%"})

        return {"answer": answer, "sources": sources, "status": "success"}
    except Exception as e:
        print(f"Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "SaaS Support Copilot API is running!"}