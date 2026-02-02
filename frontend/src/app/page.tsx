"use client";
import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function ChatPage() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<{ role: string; content: string; sources?: any[] }[]>([]);
  const [loading, setLoading] = useState(false);

  // Redirect if not logged in - protects the route
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

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
        body: JSON.stringify({ query: userMessage.content }),
      });

      const data = await res.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.answer, 
        sources: data.sources 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to backend." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="p-4 bg-white shadow flex justify-between items-center">
        <h1 className="text-xl font-bold text-blue-600">SaaS Copilot</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">Welcome, {user}!</span>
          <button onClick={logout} className="text-sm bg-red-500 text-white px-3 py-1 rounded">Logout</button>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-lg ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white border text-gray-800'}`}>
              <p>{m.content}</p>
              {/* Mandatory Source Display */}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t text-xs text-gray-500">
                  <p className="font-semibold">Sources:</p>
                  <ul className="list-disc ml-4">
                    {m.sources.map((s: any, idx: number) => (
                      <li key={idx}>{s.question}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-sm text-gray-400 animate-pulse">AI is thinking...</p>}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSendMessage} className="p-4 bg-white border-t flex gap-2">
        <input
          className="flex-1 border p-2 rounded outline-none focus:border-blue-500 text-black"
          placeholder="Ask about NeuroStack..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading} className="bg-blue-600 text-white px-6 py-2 rounded disabled:bg-gray-400">
          Send
        </button>
      </form>
    </div>
  );
}