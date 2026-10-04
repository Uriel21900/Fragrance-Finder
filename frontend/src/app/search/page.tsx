'use client';

import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import axios from 'axios';
import FragranceCard from '@/components/FragranceCard';
import SearchBar from '@/components/SearchBar';
import { FragranceData, FragranceVariant, Price } from '@/types';

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get('q') || '';
  const initialBrand = searchParams.get('brand') || '';
  
  const [brandFilter, setBrandFilter] = useState(initialBrand);
  
  const [results, setResults] = useState<FragranceData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchSearch() {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (q) params.append('q', q);
        if (brandFilter) params.append('brand', brandFilter);
        
        const res = await axios.get(`/api/search?${params.toString()}`);
        setResults(res.data);
      } catch (err) {
        console.error("Search failed", err);
      } finally {
        setLoading(false);
      }
    }
    
    if (q || brandFilter) {
      fetchSearch();
    } else {
      setLoading(false);
      setResults([]);
    }
  }, [q, brandFilter]);

  return (
    <div className="w-full flex flex-col pt-8 pb-32">
      <div className="mb-12 flex flex-col md:flex-row gap-4 items-center">
        <div className="w-full md:flex-grow">
          <SearchBar initialQuery={q} />
        </div>
        <div className="w-full md:w-64">
          <select 
            value={brandFilter}
            onChange={(e) => setBrandFilter(e.target.value)}
            className="w-full bg-black/40 border border-white/10 rounded-full px-6 py-4 text-white focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/50 appearance-none"
          >
            <option value="">All Brands</option>
            <option value="Creed">Creed</option>
            <option value="Parfums De Marly">Parfums De Marly</option>
            <option value="Tom Ford">Tom Ford</option>
            <option value="Dior">Dior</option>
            <option value="Maison Francis Kurkdjian">Maison Francis Kurkdjian</option>
            <option value="Yves Saint Laurent">Yves Saint Laurent</option>
            <option value="Armaf">Armaf</option>
            <option value="Xerjoff">Xerjoff</option>
            <option value="Roja Parfums">Roja Parfums</option>
            <option value="Initio Parfums Prives">Initio</option>
            <option value="Chanel">Chanel</option>
            <option value="Versace">Versace</option>
          </select>
        </div>
      </div>
      
      {loading ? (
        <div className="text-center text-white/50 mt-12">Searching global markets for &quot;{q}&quot;...</div>
      ) : results.length > 0 ? (
        <div>
          <h2 className="text-xl font-medium text-white mb-6">Found {results.length} matches for &quot;{q}&quot;</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {results.map((frag) => {
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
        </div>
      ) : (
        <div className="text-center text-white/50 mt-12">
          No fragrances found matching &quot;{q}&quot;. Try searching for the brand or a simpler name.
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<div className="w-full mt-24 text-center text-white/50">Loading search...</div>}>
      <SearchContent />
    </Suspense>
  );
}
