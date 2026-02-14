import os, time, traceback, io
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from huggingface_hub import InferenceClient
from pypdf import PdfReader

# Custom Modules
from database import get_db, engine
import models
# FIX: Import the new direct search function
from rag_engine import search_similar_documents, index_document
from dotenv import load_dotenv

load_dotenv()

# 1. Create Tables in Postgres
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="SaaS Support Copilot Pro")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AI Configuration ---
TOKEN = os.getenv("HF_TOKEN", "").strip().replace('"', '').replace("'", "")
client = InferenceClient(api_key=TOKEN)
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

# --- Pydantic Models ---
class UserAuth(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class ChatRequest(BaseModel):
    query: str
    username: str
    chat_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    status: str

# --- Auth Endpoints ---

@app.post("/signup")
async def signup(user_data: UserAuth, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    new_user = models.User(
        username=user_data.username,
        password=user_data.password, 
        email=user_data.email
    )
    db.add(new_user)
    db.commit()
    return {"status": "success"}

@app.post("/login")
async def login(creds: UserAuth, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == creds.username, 
        models.User.password == creds.password
    ).first()
    
    if user:
        return {"status": "success", "username": user.username}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- Document Upload Endpoint ---

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    username: str = Form(...)
):
    try:
        print(f"📂 Received file: {file.filename} from {username}")
        
        content = await file.read()
        text = ""
        
        if file.filename.endswith(".pdf"):
            pdf = PdfReader(io.BytesIO(content))
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        else:
            text = content.decode("utf-8")
            
        if not text.strip():
            raise HTTPException(status_code=400, detail="File is empty or unreadable")

        metadata = {"filename": file.filename, "user_id": username, "type": "upload"}
        count = index_document(text, metadata)
        
        return {"status": "success", "chunks": count, "filename": file.filename}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# --- Chat Endpoint (FIXED) ---

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    user_obj = db.query(models.User).filter(models.User.username == request.username).first()
    
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found. Please log in again.")

    # 1. Save User Message
    user_msg = models.ChatHistory(
        chat_id=request.chat_id, 
        role="user", 
        content=request.query, 
        user_id=user_obj.id
    )
    db.add(user_msg)
    db.commit()

    # 2. Greeting Check
    if request.query.lower().strip() in ["hi", "hello", "hey"]:
        return {"answer": f"Hi {request.username}! I'm ready to help with your documents.", "sources": [], "status": "greeting"}

    try:
        # 3. Retrieval from Supabase (USING NEW DIRECT FUNCTION)
        # This fixes the NotImplementedError
        valid_results = search_similar_documents(request.query, k=4)

        if not valid_results:
            return {"answer": "I couldn't find relevant info in your uploaded documents.", "sources": [], "status": "no_context"}

        # 4. Generate Answer
        context_text = "\n\n".join([f"Source ({doc.metadata.get('filename', 'System')}): {doc.page_content}" for doc, _ in valid_results])
        
        system_prompt = (
            "You are a helpful SaaS Copilot. Answer the user's question using ONLY the context below. "
            "Always cite the source filename when stating a fact. "
            f"\n\nContext:\n{context_text}"
        )

        response = client.chat_completion(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ],
            max_tokens=500,
            temperature=0.1
        )
        answer = response.choices[0].message.content

        # 5. Save Assistant Reply
        bot_msg = models.ChatHistory(
            chat_id=request.chat_id, 
            role="assistant", 
            content=answer, 
            user_id=user_obj.id
        )
        db.add(bot_msg)
        db.commit()

        # 6. Format Sources
        sources = [
            {"question": d.metadata.get("filename", "FAQ"), "score": f"{int(score * 100)}%"} 
            for d, score in valid_results
        ]
        
        return {"answer": answer, "sources": sources, "status": "success"}

    except Exception as e:
        traceback.print_exc()
        return {"answer": "I encountered an error. Please check logs.", "sources": [], "status": "error"}

# --- History Endpoints ---

@app.get("/chats/{username}")
async def get_chats(username: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user: return []
    chats = db.query(models.ChatHistory.chat_id).filter(models.ChatHistory.user_id == user.id).distinct().all()
    return [c[0] for c in chats]

@app.get("/history/{username}/{chat_id}")
async def get_history(username: str, chat_id: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user: return []
    
    msgs = db.query(models.ChatHistory).filter(
        models.ChatHistory.chat_id == chat_id,
        models.ChatHistory.user_id == user.id
    ).order_by(models.ChatHistory.timestamp).all()
    
    return [{"role": m.role, "content": m.content} for m in msgs]