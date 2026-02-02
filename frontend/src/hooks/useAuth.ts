import { useState } from 'react';
import { useRouter } from 'next/navigation';

export const useAuth = () => {
  const [user, setUser] = useState<any>(null);
  const router = useRouter();

  const login = async (username: string, password: string) => {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.token); // Save token for persistence
      setUser(data.username);
      router.push('/chat'); // Redirect to chat on success
    } else {
      alert("Invalid login!");
    }
  };

  return { user, login };
};