import os, sqlite3, time, traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_engine import get_retriever
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()
app = FastAPI(title="SaaS Support Copilot Pro")

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
    cursor.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, email TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, chat_id TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

# --- AI Configuration ---
TOKEN = os.getenv("HF_TOKEN", "").strip().replace('"', '').replace("'", "")
client = InferenceClient(api_key=TOKEN)
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

# --- Data Models ---
class ChatRequest(BaseModel):
    query: str
    username: str
    chat_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    status: str

# MISSING MODEL RESTORED
class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

def save_message(username, chat_id, role, content):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (username, chat_id, role, content) VALUES (?, ?, ?, ?)", 
                       (username, chat_id, role, content))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

# --- Auth Endpoints (RESTORED) ---

@app.post("/signup")
async def signup(user: UserAuth):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                       (user.username, user.password, user.email))
        conn.commit()
        return {"status": "success", "message": "User created"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
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

@app.get("/chats/{username}")
async def get_user_chats(username: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT chat_id FROM chat_history WHERE username = ? ORDER BY timestamp DESC", (username,))
    chats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chats

@app.get("/history/{username}/{chat_id}")
async def get_chat_history(username: str, chat_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT role, content FROM chat_history WHERE username = ? AND chat_id = ? ORDER BY timestamp ASC", (username, chat_id))
    history = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
    conn.close()
    return history

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    save_message(request.username, request.chat_id, "user", request.query)
    
    # 1. Greeting Handler
    if request.query.lower().strip() in ["hi", "hello", "hey", "good morning"]:
        msg = f"Hello {request.username}! I'm your NeuroStack Copilot. How can I help?"
        save_message(request.username, request.chat_id, "assistant", msg)
        return {"answer": msg, "sources": [], "status": "greeting"}

    try:
        # 2. Retrieval
        vector_db = get_retriever()
        docs_and_scores = vector_db.similarity_search_with_score(request.query, k=3)
        valid_results = [res for res in docs_and_scores if res[1] < 1.1]

        if not valid_results:
            msg = "I'm sorry, I couldn't find any information on that in our documentation."
            save_message(request.username, request.chat_id, "assistant", msg)
            return {"answer": msg, "sources": [], "status": "no_context"}

        # 3. Generation
        context = "\n\n".join([res[0].page_content for res in valid_results])
        answer = ""
        
        for attempt in range(2):
            try:
                print(f"DEBUG: AI Attempt {attempt + 1}...")
                response = client.chat_completion(
                    model=MODEL_ID,
                    messages=[
                        {"role": "system", "content": f"Use this context to answer: {context}"},
                        {"role": "user", "content": request.query}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
                answer = response.choices[0].message.content
                if answer: break
            except Exception as ai_err:
                print(f"AI Error: {ai_err}")
                time.sleep(1)

        if not answer:
            return {"answer": "The AI is currently busy. Please try again.", "sources": [], "status": "error"}

        # 4. Success
        save_message(request.username, request.chat_id, "assistant", answer)
        
        sources = [
            {"question": d.metadata.get("question"), "score": f"{max(0, 100 - int(score * 50))}%"} 
            for d, score in valid_results
        ]
        
        return {"answer": answer, "sources": sources, "status": "success"}

    except Exception as e:
        print("--- CRITICAL ERROR TRACEBACK ---")
        traceback.print_exc()
        return {"answer": "I encountered an internal error. Check your terminal for logs.", "sources": [], "status": "error"}

@app.get("/")
def read_root():
    return {"message": "API Running"}