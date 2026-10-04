'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import FragranceCard from './FragranceCard';
import { FragranceData, FragranceVariant, Price } from '@/types';
import { Flame } from 'lucide-react';

export default function TrendingSection() {
  const [trending, setTrending] = useState<FragranceData[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'niche' | 'designer' | 'clone'>('all');

  useEffect(() => {
    async function fetchTrending() {
      try {
        const res = await axios.get('/api/trending');
        setTrending(res.data);
      } catch (err) {
        console.error("Failed to fetch trending", err);
      } finally {
        setLoading(false);
      }
    }
    fetchTrending();
  }, []);

  const filteredFragrances = trending.filter(frag => {
    if (activeTab === 'all') return true;
    if (activeTab === 'niche') return frag.market_segment === 'niche' || frag.market_segment === 'ultra_niche';
    if (activeTab === 'designer') return frag.market_segment === 'designer' || frag.market_segment === 'entry_luxury';
    if (activeTab === 'clone') return frag.is_dupe || frag.market_segment === 'clone' || frag.market_segment === 'middle_eastern';
    return true;
  });

  if (loading) {
    return (
      <section className="w-full mt-12 text-center text-white/50">
        <div className="flex justify-center items-center gap-3">
          <div className="w-5 h-5 border-2 border-gold border-t-transparent rounded-full animate-spin"></div>
          <span>Loading curated fragrances...</span>
        </div>
      </section>
    );
  }

  return (
    <section className="w-full mt-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-gold text-xs font-bold uppercase tracking-wider mb-1">
            <Flame size={16} />
            <span>Verified Market Prices & Stock</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-black tracking-tight text-white">
            Trending & Most Popular Scents
          </h2>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 bg-white/5 p-1.5 rounded-full border border-white/10 self-start md:self-auto">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
              activeTab === 'all' 
                ? 'bg-gold text-black shadow-lg shadow-gold/20' 
                : 'text-white/60 hover:text-white'
            }`}
          >
            All Featured
          </button>
          <button
            onClick={() => setActiveTab('niche')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
              activeTab === 'niche' 
                ? 'bg-gold text-black shadow-lg shadow-gold/20' 
                : 'text-white/60 hover:text-white'
            }`}
          >
            Niche Luxury
          </button>
          <button
            onClick={() => setActiveTab('designer')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
              activeTab === 'designer' 
                ? 'bg-gold text-black shadow-lg shadow-gold/20' 
                : 'text-white/60 hover:text-white'
            }`}
          >
            Designer
          </button>
          <button
            onClick={() => setActiveTab('clone')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
              activeTab === 'clone' 
                ? 'bg-gold text-black shadow-lg shadow-gold/20' 
                : 'text-white/60 hover:text-white'
            }`}
          >
            Top Clones
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredFragrances.map((frag) => {
          // Find lowest price and total stores
          let lowestPrice = Infinity;
          let totalStores = 0;
          frag.variants?.forEach((v: FragranceVariant) => {
            if (v.prices && v.prices.length > 0) {
              totalStores += v.prices.length;
              v.prices.forEach((p: Price) => {
                if (p.price_amount < lowestPrice) {
                  lowestPrice = p.price_amount;
                }
              });
            }
          });

          return (
            <FragranceCard
              key={frag.dna_id}
              id={frag.dna_id}
              brand={frag.brand_name}
              name={frag.canonical_name}
              imageUrl={frag.image_url}
              marketSegment={frag.market_segment}
              gender={frag.gender}
              isDupe={frag.is_dupe}
              inspiredBy={frag.inspired_by}
              storeCount={totalStores}
              price={lowestPrice !== Infinity ? `$${lowestPrice.toFixed(2)}` : 'In Stock'}
            />
          );
        })}
      </div>
    </section>
  );
}
