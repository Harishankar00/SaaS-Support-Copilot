import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from rag_engine import get_retriever
from langchain_huggingface import HuggingFaceEndpoint
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="SaaS Support Copilot API")

# Enable CORS so your Next.js frontend can talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the LLM (Using a free Hugging Face model)
# Make sure you have HF_TOKEN in your .env file
llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.3",
    huggingfacehub_api_token=os.getenv("HF_TOKEN"),
    temperature=0.1, # Low temperature for factual, grounded answers
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    status: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        retriever = get_retriever()
        # 1. Retrieve the top 3 relevant chunks from FAISS
        docs = retriever.invoke(request.query)
        
        if not docs:
            return {"answer": "I'm sorry, I couldn't find any information regarding that in our documentation.", "sources": [], "status": "no_context"}

        # 2. Build the context for the LLM
        context_text = "\n\n".join([d.page_content for d in docs])
        
        # 3. Prompt Engineering for Hallucination Blocking
        prompt = f"""
        You are a helpful SaaS Support Assistant. Use ONLY the following pieces of context to answer the user's question.
        If the answer is not in the context, politely say that you don't know and suggest contacting support.
        Do not make up information.

        Context:
        {context_text}

        User Question: {request.query}
        Answer:"""

        # 4. Generate Answer
        response = llm.invoke(prompt)
        
        return {
            "answer": response.strip(),
            "sources": [{"question": d.metadata["question"], "answer": d.metadata["answer"]} for d in docs],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "SaaS Support Copilot API is running!"}

# Note: Add your Signup/Login logic here using JWT for the final submission
from fastapi import Body

# Mock user for testing - you can expand this later
MOCK_USER = {"username": "hari", "password": "password123"}

@app.post("/login")
async def login(credentials: dict = Body(...)):
    if credentials.get("username") == MOCK_USER["username"] and \
       credentials.get("password") == MOCK_USER["password"]:
        return {"status": "success", "username": credentials.get("username"), "token": "fake-jwt-token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")



# Temporary in-memory user store
users_db = []

@app.post("/signup")
async def signup(user_data: dict = Body(...)):
    # Check if username exists
    if any(u['username'] == user_data['username'] for u in users_db):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    users_db.append(user_data)
    return {"status": "success", "message": "User registered"}

@app.post("/login")
async def login(credentials: dict = Body(...)):
    # Look for user in our "database"
    user = next((u for u in users_db if u['username'] == credentials['username']), None)
    
    if user and user['password'] == credentials['password']:
        return {"status": "success", "username": user['username'], "token": "fake-jwt-token"}
    
    raise HTTPException(status_code=401, detail="Invalid credentials")