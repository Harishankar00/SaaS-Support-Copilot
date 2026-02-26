# 🚀 SaaS Support Copilot Pro

Welcome to **SaaS Support Copilot Pro** — a Retrieval-Augmented Generation (RAG) assistant that reads your company docs, FAQs, and manuals and returns accurate, source-backed answers.

Live demo (frontend): https://saa-s-support-copilot-3bunj2aa2-yoyoharishankar-6711s-projects.vercel.app/login  
Backend API: https://harishankar000-saas-copilot-backend.hf.space

## Features
- Full authentication (PostgreSQL-backed).
- Persistent chat history and session grouping.
- RAG pipeline: document ingestion → text splitting → vectorization → cloud vector store.
- Hybrid search with direct Supabase RPC queries for high-precision retrieval.
- Llama 3 inference via Hugging Face for reasoning.

## Uploading Knowledge (preferred format)
For best results, upload a .txt file whose contents are a JSON array of QA objects. Example:

```json
[
  {
    "question": "What is the refund policy?",
    "answer": "We offer a 30-day money-back guarantee on all pro plans. No questions asked."
  },
  {
    "question": "How do I reset my password?",
    "answer": "Click the 'Forgot Password' link on the login page and follow the email instructions."
  }
]
```

Steps:
1. Save the JSON array to a file (e.g., `knowledge_base.txt`).
2. In the app chat, click the 📎 paperclip and upload the file.
3. Wait for the success confirmation and start querying.

## Tech Stack
- Frontend: Next.js 14, React, Tailwind CSS (+ @tailwindcss/typography). Hosted on Vercel.  
- Backend: FastAPI (Python).  
- Database & Vector Store: Supabase (Postgres + pgvector).  
- Embeddings & RAG: LangChain + Hugging Face (embeddings: all-MiniLM-L6-v2).  
- Model inference: meta-llama/Llama-3.1-8B-Instruct via Hugging Face.  
- Deployment: Hugging Face Spaces (Docker).

## Run Locally

1) Clone
```bash
git clone https://github.com/Harishankar00/SaaS-Support-Copilot
cd SaaS-Support-Copilot
```

2) Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Create `.env` in `backend/` with:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/postgres
HF_TOKEN=your_huggingface_api_token
```
Start server:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

3) Frontend
```bash
cd ../frontend
npm install
```
Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```
Start UI:
```bash
npm run dev
```
Open http://localhost:3000

## Notes
- Ensure Supabase and Hugging Face credentials are valid and have required permissions.
- Use the JSON `.txt` upload method for structured FAQ ingestion to improve retrieval accuracy.

License and contribution details live in the repository.
