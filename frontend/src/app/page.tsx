"use client";
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{ role: string; content: string; sources?: any[] }[]>([]);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // 1. Load Chat History on Login
  useEffect(() => {
    if (!user) {
      router.push('/login');
    } else {
      fetch(`${process.env.NEXT_PUBLIC_API_URL}/history/${user}`)
        .then(res => res.json())
        .then(data => setMessages(data));
    }
  }, [user, router]);

  // 2. Auto-scroll to bottom
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { role: 'user', content: query };
    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.content, username: user }),
      });

      const data = await res.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.answer, 
        sources: data.sources 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to AI server." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="flex h-screen bg-[#F9FAFB] text-gray-900 font-sans">
      {/* Side Navigation (Gemini Style) */}
      <aside className="w-64 bg-[#1F2937] text-white flex flex-col p-4 hidden md:flex">
        <h2 className="text-xl font-bold mb-8 text-blue-400">NeuroStack</h2>
        <nav className="flex-1 space-y-2 overflow-y-auto">
          <p className="text-xs font-semibold text-gray-500 uppercase">Recent Chats</p>
          {/* We can map history here to show list items like ChatGPT */}
          <div className="p-2 hover:bg-gray-700 rounded cursor-pointer text-sm truncate">
            Documentation Q&A
          </div>
        </nav>
        <button onClick={logout} className="mt-auto p-2 bg-red-600/20 text-red-400 rounded hover:bg-red-600/30">
          Logout
        </button>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col max-w-5xl mx-auto w-full">
        {/* Header */}
        <header className="p-6 border-b bg-white/50 backdrop-blur-md sticky top-0 flex justify-between">
          <h1 className="text-lg font-semibold">SaaS Support Copilot</h1>
          <span className="text-sm text-gray-500 italic">Connected to Llama-3</span>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] px-5 py-4 rounded-2xl shadow-sm ${
                m.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white border border-gray-100 rounded-tl-none'
              }`}>
                <p className="leading-relaxed">{m.content}</p>
                
                {/* 3. Similarity Score Badges */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-gray-50">
                    <p className="text-[10px] font-bold text-gray-400 uppercase mb-2">Retrieved Sources</p>
                    <div className="flex flex-wrap gap-2">
                      {m.sources.map((s: any, idx: number) => (
                        <div key={idx} className="px-2 py-1 bg-green-50 text-green-700 text-[10px] rounded-full font-medium border border-green-100">
                          {s.score} Match: {s.question.substring(0, 30)}...
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={scrollRef} />
          {loading && (
            <div className="flex justify-start animate-pulse">
              <div className="bg-gray-200 h-8 w-24 rounded-full" />
            </div>
          )}
        </div>

        {/* Input Footer */}
        <div className="p-6 bg-gradient-to-t from-white via-white to-transparent">
          <form onSubmit={handleSendMessage} className="relative flex items-center">
            <input
              className="w-full bg-white border-2 border-gray-200 rounded-2xl py-4 pl-6 pr-16 focus:border-blue-500 outline-none transition-all shadow-lg"
              placeholder="Type your question about NeuroStack..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <button 
              type="submit" 
              disabled={loading}
              className="absolute right-3 p-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="="></path></svg>
              Send
            </button>
          </form>
          <p className="text-[10px] text-center mt-3 text-gray-400">AI can make mistakes. Verify important information.</p>
        </div>
      </main>
    </div>
  );
}