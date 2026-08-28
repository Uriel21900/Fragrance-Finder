'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search } from 'lucide-react';
import { motion } from 'framer-motion';

export default function SearchBar({ initialQuery = '' }: { initialQuery?: string }) {
  const [query, setQuery] = useState(initialQuery);
  const router = useRouter();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <motion.form 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      onSubmit={handleSearch} 
      className="relative w-full max-w-2xl mx-auto"
    >
      <div className="relative group">
        <div className="absolute inset-0 bg-gold/20 rounded-full blur-xl group-hover:bg-gold/30 transition-all duration-500 opacity-50"></div>
        <div className="relative flex items-center w-full glass rounded-full overflow-hidden border border-white/10 group-hover:border-gold/50 transition-all duration-300 shadow-2xl">
          <div className="pl-6 text-gray-400 group-hover:text-gold transition-colors">
            <Search size={22} />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for a luxury fragrance (e.g., Aventus, Baccarat Rouge)..."
            className="w-full bg-transparent border-none py-5 px-4 text-white placeholder-gray-500 focus:outline-none focus:ring-0 text-lg"
          />
          <button 
            type="submit" 
            className="pr-6 pl-4 text-gold hover:text-white font-medium transition-colors"
          >
            Search
          </button>
        </div>
      </div>
    </motion.form>
  );
}
