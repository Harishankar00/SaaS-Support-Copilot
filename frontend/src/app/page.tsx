"use client";
import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

// --- Types ---
interface Source {
  score: string;
  question: string;
}

interface Message {
  role: string;
  content: string;
  sources?: Source[];
}

export default function ChatPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  
  // State
  const [currentChatId, setCurrentChatId] = useState<string>("");
  const [chatList, setChatList] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 1. Stable Fetch Function (Wrapped in useCallback to fix dependency errors)
  const refreshChatList = useCallback(async () => {
    if (!user) return;
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chats/${user}`);
      if (res.ok) setChatList(await res.json());
    } catch (e) {
      console.error("Failed to fetch chats:", e);
    }
  }, [user]);

  // 2. Initial Side Effects
  useEffect(() => {
    if (!user) {
      router.push('/login');
    } else {
      refreshChatList();
      if (!currentChatId) {
        setCurrentChatId(`chat_${Date.now()}`);
      }
    }
  }, [user, router, refreshChatList, currentChatId]);

  // 3. Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // --- Actions ---

  const startNewChat = () => {
    setCurrentChatId(`chat_${Date.now()}`);
    setMessages([]);
  };

  const switchChat = async (id: string) => {
    setCurrentChatId(id);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/history/${user}/${id}`);
      if (res.ok) setMessages(await res.json());
    } catch (e) {
      console.error("Failed to load history:", e);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg: Message = { role: 'user', content: query };
    setMessages(prev => [...prev, userMsg]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: userMsg.content, 
          username: user, 
          chat_id: currentChatId 
        }),
      });

      const data = await res.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.answer, 
        sources: data.sources 
      }]);
      
      refreshChatList();
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to AI server." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    // ROOT: h-screen + overflow-hidden pins the UI to viewport
    <div className="flex h-screen w-full bg-[#0b1120] text-slate-200 overflow-hidden font-sans">
      
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full" />
      </div>

      {/* SIDEBAR */}
      <aside className="w-72 bg-slate-900/60 backdrop-blur-xl border-r border-slate-800 flex flex-col z-20 shrink-0 hidden md:flex">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">N</div>
            <h2 className="text-xl font-bold tracking-tight">NeuroStack</h2>
          </div>
          <button 
            onClick={startNewChat} 
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-xl transition-all font-bold text-sm shadow-lg shadow-blue-900/40 flex items-center justify-center gap-2"
          >
            <span>+</span> New Chat
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto px-4 space-y-2 mb-4 scrollbar-hide">
          <p className="text-[10px] font-bold text-slate-500 uppercase px-2 mb-2">Recent Sessions</p>
          {chatList.map(id => (
            <div 
              key={id} 
              onClick={() => switchChat(id)} 
              className={`p-3 rounded-xl cursor-pointer text-xs transition-all border flex items-center gap-2 ${
                currentChatId === id 
                ? 'bg-slate-800 border-slate-700 text-blue-400' 
                : 'border-transparent text-slate-500 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${currentChatId === id ? 'bg-blue-400' : 'bg-slate-600'}`} />
              Session {id.split('_')[1]?.slice(-4)}
            </div>
          ))}
        </nav>

        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-[10px] font-bold text-white border border-slate-600">
                {user.slice(0, 2).toUpperCase()}
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold truncate max-w-[100px] text-white">{user}</span>
                <span className="text-[10px] text-slate-500">Pro Plan</span>
              </div>
            </div>
            <button onClick={logout} className="text-slate-500 hover:text-red-400 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7" /></svg>
            </button>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main className="flex-1 flex flex-col h-full relative z-10">
        <header className="h-16 border-b border-slate-800/50 bg-slate-900/40 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
          <span className="text-xs font-black uppercase tracking-widest text-slate-400">Support Assistant</span>
          <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">Llama-3-8B Connected</span>
        </header>

        {/* MESSAGES AREA */}
        <div className="flex-1 overflow-y-auto p-6 md:p-12 space-y-8 custom-scrollbar">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-slate-600 opacity-60">
              <div className="w-20 h-20 bg-slate-900/50 rounded-3xl border border-slate-800 flex items-center justify-center mb-6 shadow-2xl">
                <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
              </div>
              <p className="text-sm font-medium">How can I help you with NeuroStack today?</p>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in slide-in-from-bottom-2 duration-300`}>
              <div className={`max-w-[85%] md:max-w-[70%] group`}>
                <div className={`px-6 py-4 rounded-2xl shadow-xl transition-all ${
                  m.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-tr-sm shadow-blue-900/20' 
                  : 'bg-slate-800/80 border border-slate-700 text-slate-200 rounded-tl-sm hover:border-slate-600'
                }`}>
                  <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">{m.content}</p>
                </div>
                
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2 px-1 opacity-80 group-hover:opacity-100 transition-opacity">
                    {/* FIXED: Explicit typing for map arguments */}
                    {m.sources.map((s: Source, idx: number) => (
                      <div key={idx} className="flex items-center gap-1.5 px-3 py-1 bg-slate-900/50 border border-slate-700 rounded-full text-[10px] font-bold text-blue-400">
                        <span className={`w-1.5 h-1.5 rounded-full ${parseInt(s.score) > 80 ? 'bg-green-400' : 'bg-yellow-400'}`} />
                        {s.score} Match: <span className="text-slate-500 ml-1">{s.question.substring(0, 20)}...</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={scrollRef} className="h-4" />
        </div>

        {/* INPUT FOOTER */}
        <div className="shrink-0 p-6 md:p-8 bg-gradient-to-t from-[#0b1120] via-[#0b1120] to-transparent z-20">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl opacity-10 group-focus-within:opacity-30 blur-xl transition duration-500" />
            <div className="relative flex">
              <input
                className="w-full bg-slate-900/90 border border-slate-700/50 rounded-2xl py-4 pl-6 pr-16 focus:outline-none focus:border-blue-500/50 transition-all text-sm md:text-base text-slate-200 placeholder:text-slate-500 shadow-2xl"
                placeholder="Ask a question about NeuroStack..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button 
                type="submit" 
                disabled={loading} 
                className="absolute right-2 top-2 bottom-2 aspect-square bg-blue-600 hover:bg-blue-500 text-white rounded-xl flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 12h14M12 5l7 7-7 7" /></svg>
                )}
              </button>
            </div>
          </form>
          <p className="text-[10px] text-center mt-4 text-slate-500 font-medium uppercase tracking-widest opacity-40">AI responses generated from documentation</p>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #334155; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
      `}</style>
    </div>
  );
}