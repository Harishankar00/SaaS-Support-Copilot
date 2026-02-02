import os
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from rag_engine import get_retriever
from dotenv import load_dotenv
# Use the official client to bypass LangChain version conflicts
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

# Direct client is more stable for free-tier inference
client = InferenceClient(api_key=os.getenv("HF_TOKEN"))
# Swapping to a highly stable, current model to avoid the 410 Deprecation error
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

# --- In-Memory Database ---
# Persistent test user for debugging
users_db = [{"username": "hari", "password": "password123", "email": "hari@test.com"}]

# --- Endpoints ---

@app.get("/")
def read_root():
    return {"message": "SaaS Support Copilot API is running!"}

@app.post("/signup")
async def signup(user: UserAuth):
    if any(u['username'] == user.username for u in users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db.append(user.model_dump())
    return {"status": "success", "message": "User registered"}

@app.post("/login")
async def login(credentials: UserAuth):
    user = next((u for u in users_db if u['username'] == credentials.username), None)
    if user and user['password'] == credentials.password:
        return {"status": "success", "username": user['username'], "token": "fake-jwt-token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        print(f"DEBUG: Received query: {request.query}")
        
        # 1. Retrieve FAQ context
        retriever = get_retriever()
        docs = retriever.invoke(request.query)
        
        if not docs:
            return {"answer": "I don't have information on that in our documentation.", "sources": [], "status": "no_context"}

        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 2. Generate Grounded Answer
        try:
            chat_completion = client.chat_completion(
                model=MODEL_ID,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a SaaS Support Assistant. Use ONLY the provided context. If the answer isn't there, say you don't know."
                    },
                    {
                        "role": "user", 
                        "content": f"Context: {context_text}\n\nQuestion: {request.query}"
                    }
                ],
                max_tokens=512,
                temperature=0.1
            )
            response_text = chat_completion.choices[0].message.content
        except Exception as llm_err:
            print(f"ERROR in LLM Generation: {llm_err}")
            return {"answer": "The AI is currently resetting. Please try again in a moment!", "sources": [], "status": "llm_error"}
        
        # 3. Return response with sources
        return {
            "answer": response_text.strip(),
            "sources": [{"question": d.metadata.get("question"), "answer": d.metadata.get("answer")} for d in docs],
            "status": "success"
        }
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))