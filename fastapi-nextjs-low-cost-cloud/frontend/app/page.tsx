'use client';

import { useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await axios.post('/api/chat', { query });
      setResponse(JSON.stringify(result.data, null, 2));
    } catch (error) {
      setResponse('Error: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Entertainment Agent - Practice Deployment</h1>
      
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about a show... (e.g., 'Tell me about Breaking Bad')"
            className="flex-1 p-3 border rounded-lg"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg disabled:bg-gray-400"
          >
            {loading ? 'Loading...' : 'Ask'}
          </button>
        </div>
      </form>

      {response && (
        <div className="bg-gray-100 p-4 rounded-lg">
          <h2 className="font-bold mb-2">Response:</h2>
          <pre className="whitespace-pre-wrap text-sm text-black">{response}</pre>
        </div>
      )}

      <div className="mt-8 text-sm text-gray-600">
        <p>Status: Frontend running ✓</p>
        <p>Backend: Not connected yet</p>
      </div>
    </main>
  );
}