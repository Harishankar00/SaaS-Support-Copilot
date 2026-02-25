# 🚀 SaaS Support Copilot Pro

Welcome to **SaaS Support Copilot Pro**—an intelligent, RAG-powered (Retrieval-Augmented Generation) AI assistant designed to read your company documents, FAQs, and manuals, and actually give users helpful answers instead of hallucinating nonsense.

**🟢 Live Demo (Frontend):** [Play with the live app here!](https://saa-s-support-copilot-3bunj2aa2-yoyoharishankar-6711s-projects.vercel.app/login)  
**🧠 Backend API:** [Hosted on Hugging Face Spaces](https://harishankar000-saas-copilot-backend.hf.space)

---

## ✨ Features
* **Full Authentication:** Secure login and signup backed by a PostgreSQL database.
* **Persistent Memory:** Chat history is saved per user and grouped into continuous sessions.
* **Smart RAG Engine:** Upload your documents, and the backend chops them up, converts them into mathematical vectors, and stores them in the cloud.
* **Hybrid Search:** Bypasses basic wrappers to directly query Supabase via RPC for hyper-accurate document retrieval.
* **Llama-3 Powered:** Uses `meta-llama/Llama-3.1-8B-Instruct` via Hugging Face Inference API for fast, smart reasoning.

---

## 📂 How to Feed the AI (The "Secret Menu" Upload Method)

While the AI can process standard PDFs, the **absolute best way** to get highly accurate answers for FAQs and structured data is to use our special upload method. 

Yes, it sounds a little weird, but trust the process: **You need to upload a `.txt` file, but the text inside must be formatted as JSON.**

Why? Because our backend text splitter loves plain text, but the LLM reads structured key-value pairs like an absolute genius. 

### 📝 Step-by-Step Upload Guide:
1. Create a new file on your computer and name it something like `knowledge_base.txt`.
2. Open the file and paste your data using this exact JSON array format:

```json
[
  {
    "question": "What is the refund policy?",
    "answer": "We offer a 30-day money-back guarantee on all pro plans. No questions asked."
  },
  {
    "question": "How do I reset my password?",
    "answer": "Click the 'Forgot Password' link on the login page and follow the email instructions."
  },
  {
    "question": "Do you offer API access?",
    "answer": "Yes, API access is available on the Enterprise tier. Rate limits apply."
  }
]
Save the file.

Go to the chat interface, click the 📎 Paperclip icon, and upload knowledge_base.txt.

Wait for the ✅ success toast, and start asking questions!

🛠️ Tech Stack
Frontend (The Pretty Face)
Framework: Next.js 14 (React)

Styling: Tailwind CSS + @tailwindcss/typography for beautiful Markdown rendering.

Hosting: Vercel

Backend (The Brain)
Framework: FastAPI (Python)

Database & Vector Store: Supabase (PostgreSQL + pgvector)

AI & Embeddings: LangChain + Hugging Face (all-MiniLM-L6-v2 for embeddings)

Hosting: Hugging Face Spaces (Docker)

💻 Running it Locally
Want to mess with the code? Here is how to spin it up on your own machine.

1. Clone the Repo
Bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
2. Setup the Backend
Open a terminal and navigate to the backend folder:

Bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
Create a .env file in the backend folder and add your secrets:

Code snippet
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://postgres.yourproject:password@aws-0-region.pooler.supabase.com:6543/postgres
HF_TOKEN=your_huggingface_api_token
Start the server:

Bash
uvicorn main:app --reload
3. Setup the Frontend
Open a new terminal and navigate to the frontend folder:

Bash
cd frontend
npm install
Create a .env.local file in the frontend folder:

Code snippet
NEXT_PUBLIC_API_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)
Start the UI:

Bash
npm run dev
Navigate to http://localhost:3000 and you are good to go!


***

Now that your project looks 100% legit, would you like me to show you that quick 5-line script to add to `main.py` so the backend actually *parses* those JSON text files perfectly?