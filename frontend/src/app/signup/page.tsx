"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const [formData, setFormData] = useState({ username: '', password: '', email: '' });
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Call the FastAPI backend signup endpoint
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });

    if (res.ok) {
      alert("Account created successfully! Redirecting to login...");
      router.push('/login');
    } else {
      const errorData = await res.json();
      alert(errorData.detail || "Signup failed. Please try again.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
      <form onSubmit={handleSignup} className="p-8 bg-white shadow-md rounded-lg w-96">
        <h2 className="text-2xl font-bold mb-6 text-center text-green-600">Create Account</h2>
        <input
          type="text"
          placeholder="Username"
          className="w-full p-2 mb-4 border rounded"
          onChange={(e) => setFormData({ ...formData, username: e.target.value })}
          required
        />
        <input
          type="email"
          placeholder="Email Address"
          className="w-full p-2 mb-4 border rounded"
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Password"
          className="w-full p-2 mb-6 border rounded"
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          required
        />
        <button type="submit" className="w-full bg-green-600 text-white p-2 rounded hover:bg-green-700">
          Sign Up
        </button>
        <p className="mt-4 text-sm text-center">
          Already have an account? <a href="/login" className="text-blue-500">Login here</a>
        </p>
      </form>
    </div>
  );
}