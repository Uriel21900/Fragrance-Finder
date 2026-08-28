'use client';

import { useState, useEffect } from "react";
import axios from "axios";
import { BrandData } from "@/types";
import { useRouter } from "next/navigation";

export default function BrandsPage() {
  const [brands, setBrands] = useState<BrandData[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function fetchBrands() {
      try {
        const res = await axios.get("/api/brands");
        setBrands(res.data);
      } catch (err) {
        console.error("Failed to fetch brands", err);
      } finally {
        setLoading(false);
      }
    }
    fetchBrands();
  }, []);

  // Group brands by first letter
  const groupedBrands: Record<string, BrandData[]> = {};
  brands.forEach(b => {
    const firstLetter = b.name.charAt(0).toUpperCase();
    const letter = /[A-Z]/.test(firstLetter) ? firstLetter : '#';
    if (!groupedBrands[letter]) groupedBrands[letter] = [];
    groupedBrands[letter].push(b);
  });

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-8">Brand Directory</h1>
      
      {loading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-white/10 w-1/4 rounded"></div>
          <div className="h-4 bg-white/10 w-1/2 rounded"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {Object.keys(groupedBrands).sort().map(letter => (
            <div key={letter} className="mb-6">
              <h2 className="text-2xl font-bold text-orange-500 border-b border-white/10 pb-2 mb-4">{letter}</h2>
              <ul className="space-y-2">
                {groupedBrands[letter].map(brand => (
                  <li key={brand.name}>
                    <button 
                      onClick={() => router.push(`/search?q=${encodeURIComponent(brand.name)}`)}
                      className="text-white/70 hover:text-white hover:underline text-sm text-left w-full transition-colors"
                    >
                      {brand.name}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
