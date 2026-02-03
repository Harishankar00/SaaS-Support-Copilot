import os
import sqlite3
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from rag_engine import get_retriever
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

app = FastAPI(title="SaaS Support Copilot API")

# Enable CORS for Next.js communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SQLite Database Setup ---
DB_PATH = "users.db"

def init_db():
    """Creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT
        )
    ''')
    # Pre-seed with 'hari' for easy testing
    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                       ("hari", "password123", "hari@test.com"))
    except sqlite3.IntegrityError:
        pass # User already exists
    conn.commit()
    conn.close()

init_db()

# --- AI Configuration ---
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

# --- Data Models ---
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    status: str

class UserAuth(BaseModel):
    username: str
    password: str
    email: str = None

# --- Auth Endpoints (Persistent with SQLite) ---

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

# --- RAG Endpoint ---

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"DEBUG: Received query: {request.query}")
        
        # 1. Retrieve FAQ context via LangChain retriever
        retriever = get_retriever()
        docs = retriever.invoke(request.query)
        
        if not docs:
            return {"answer": "I don't have information on that.", "sources": [], "status": "no_context"}

        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. Generate Answer using Llama-3
        try:
            chat_completion = client.chat_completion(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": "You are a SaaS Support Assistant. Use ONLY the provided context. If the answer isn't there, say you don't know."},
                    {"role": "user", "content": f"Context: {context_text}\n\nQuestion: {request.query}"}
                ],
                max_tokens=512,
                temperature=0.1
            )
            response_text = chat_completion.choices[0].message.content
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"answer": "AI is busy. Try again!", "sources": [], "status": "llm_error"}
        
        return {
            "answer": response_text.strip(),
            "sources": [{"question": d.metadata.get("question"), "answer": d.metadata.get("answer")} for d in docs],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "SaaS Support Copilot API is running!"}