"use client";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Source {
  question: string;
  score: string;
}

export default function ChatPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [chatId, setChatId] = useState<string>("");
  const [sources, setSources] = useState<Source[]>([]);
  
  // Sidebar State
  const [chatList, setChatList] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. Initialize Chat & Fetch History
  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }

    const today = new Date().toISOString().split("T")[0];
    const newChatId = `chat_${Date.now()}`;
    setChatId(newChatId);

    // Fetch previous chat sessions
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats/${user}`)
      .then((res) => res.json())
      .then((data) => setChatList(data || []))
      .catch((err) => console.error("Failed to load chats:", err));

  }, [user, router]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 2. Handle File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    
    const file = e.target.files[0];
    setUploading(true);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("username", user || "guest");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Upload failed");
      
      const data = await res.json();
      
      setMessages(prev => [...prev, {
        role: "assistant",
        content: `✅ **Processed ${file.name}**\nI've indexed ${data.chunks} chunks. You can now ask questions about this document!`
      }]);
      
    } catch (err) {
      alert("Failed to upload document. Please try again.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // 3. Send Message Logic
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMsg,
          username: user,
          chat_id: chatId,
        }),
      });

      const data = await res.json();
      
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
      if (data.sources) setSources(data.sources);

      if (!chatList.includes(chatId)) {
        setChatList(prev => [chatId, ...prev]);
      }

    } catch (err) {
      setMessages((prev) => [...prev, { role: "assistant", content: "⚠️ Error connecting to server." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#0b1120] text-slate-200 font-sans overflow-hidden">
      
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900/50 backdrop-blur-xl border-r border-slate-800 flex flex-col hidden md:flex">
        <div className="p-6 border-b border-slate-800/50 flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">N</div>
          <h1 className="font-bold text-lg tracking-tight">NeuroStack</h1>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <button 
            onClick={() => {
              const newId = `chat_${Date.now()}`;
              setChatId(newId);
              setMessages([]);
              setSources([]);
            }}
            className="w-full py-3 px-4 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-xl transition-all text-sm font-semibold flex items-center gap-2 mb-4"
          >
            <span>+</span> New Chat
          </button>
          
          <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2 ml-2">Recent</div>
          {chatList.filter(id => id && id.includes('_')).map((id) => (
             <div 
               key={id} 
               onClick={() => setChatId(id)}
               className={`p-3 rounded-xl cursor-pointer text-sm truncate transition-all ${chatId === id ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}
             >
               {new Date(parseInt(id.split('_')[1])).toLocaleDateString()} Session
             </div>
          ))}
        </div>

        <div className="p-4 border-t border-slate-800/50">
          <button onClick={logout} className="flex items-center gap-3 w-full p-2 hover:bg-red-500/10 rounded-lg text-slate-400 hover:text-red-400 transition-colors text-sm">
            <span className="w-2 h-2 rounded-full bg-green-500"></span>
            {user} (Logout)
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
           <div className="absolute top-[-10%] right-[-5%] w-[30%] h-[30%] bg-blue-600/10 blur-[100px] rounded-full" />
           <div className="absolute bottom-[-10%] left-[-5%] w-[30%] h-[30%] bg-indigo-600/10 blur-[100px] rounded-full" />
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 relative z-10 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-50 space-y-4">
              <div className="w-20 h-20 bg-slate-800/50 rounded-3xl flex items-center justify-center mb-4 backdrop-blur-sm border border-slate-700">
                <span className="text-4xl">👋</span>
              </div>
              <h2 className="text-2xl font-bold text-white">Welcome, {user}</h2>
              <p className="max-w-md text-slate-400">
                I'm your SaaS Copilot. Upload a PDF or ask me anything about your documents!
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] md:max-w-[70%] p-4 rounded-2xl shadow-xl backdrop-blur-sm border ${
                  msg.role === "user" 
                    ? "bg-blue-600 text-white border-blue-500 rounded-br-none" 
                    : "bg-slate-800/80 text-slate-200 border-slate-700 rounded-bl-none"
                }`}>
                  {/* FIX IS HERE: Wrapped ReactMarkdown in a div with the className */}
                  <div className="prose prose-invert text-sm leading-relaxed max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && (
             <div className="flex justify-start">
               <div className="px-4 py-3 bg-slate-800/50 rounded-2xl rounded-bl-none border border-slate-700 flex items-center gap-2">
                 <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}/>
                 <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}/>
                 <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}/>
               </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6 bg-slate-900/50 backdrop-blur-md border-t border-slate-800 relative z-20">
          <div className="max-w-4xl mx-auto relative flex items-center gap-3">
            <input 
              type="file" 
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.txt,.md"
              className="hidden"
            />
            
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className={`p-3.5 rounded-xl transition-all border border-slate-700 ${
                uploading 
                  ? "bg-blue-500/20 text-blue-400 animate-pulse cursor-wait" 
                  : "bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
              }`}
              title="Upload Document"
            >
              {uploading ? "⏳" : "📎"}
            </button>

            <input
              type="text"
              className="flex-1 bg-slate-950/50 border border-slate-800 text-slate-200 rounded-xl px-5 py-3.5 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all placeholder:text-slate-600 shadow-inner"
              placeholder={uploading ? "Processing file..." : "Ask about your documents..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              disabled={loading || uploading}
            />
            
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="p-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl font-bold shadow-lg shadow-blue-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed transform active:scale-95"
            >
              ➤
            </button>
          </div>
          
          {sources.length > 0 && (
            <div className="max-w-4xl mx-auto mt-3 flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {sources.map((source, i) => (
                <div key={i} className="flex-shrink-0 text-xs px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-full text-slate-400 flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                  <span className="truncate max-w-[150px]">{source.question}</span>
                  <span className="bg-slate-700 px-1.5 rounded text-[10px]">{source.score}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}