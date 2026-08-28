'use client';

import { useState, useEffect } from "react";
import axios from "axios";
import { FragranceData } from "@/types";
import FragranceCard from "@/components/FragranceCard";

export default function TrendingPage() {
  const [trending, setTrending] = useState<FragranceData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchTrending() {
      try {
        const res = await axios.get("http://localhost:8000/api/trending/influencers");
        setTrending(res.data);
      } catch (err) {
        console.error("Failed to fetch trending", err);
      } finally {
        setLoading(false);
      }
    }
    fetchTrending();
  }, []);

  return (
    <div className="container mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Trending on #FragranceTok</h1>
      <p className="text-white/60 mb-8">
        The hottest fragrances right now, mentioned by top influencers and reviewers.
      </p>

      {loading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-40 bg-white/5 rounded-xl"></div>
          <div className="h-40 bg-white/5 rounded-xl"></div>
          <div className="h-40 bg-white/5 rounded-xl"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {trending.map((frag) => {
            let lowestPrice = 0;
            const conc = "EDP";
            if (frag.variants && frag.variants.length > 0) {
                const varPrices = frag.variants.map(v => v.prices.map(p => p.price_amount)).flat();
                if (varPrices.length > 0) {
                    lowestPrice = Math.min(...varPrices);
                }
            }

            return (
              <div key={frag.dna_id} className="relative">
                <div className="absolute -top-3 left-4 z-10 bg-gradient-to-r from-orange-500 to-red-500 text-white text-xs font-bold px-3 py-1 rounded-full shadow-lg">
                  Mentioned by: {frag.influencer_mentions}
                </div>
                <FragranceCard 
                  id={frag.dna_id}
                  brand={frag.brand_name}
                  name={frag.canonical_name}
                  imageUrl={frag.image_url}
                  marketSegment={frag.market_segment}
                  price={lowestPrice > 0 ? `$${lowestPrice.toFixed(2)}` : "In Stock"}
                  concentration={conc}
                  isDupe={frag.is_dupe}
                  inspiredBy={frag.inspired_by}
                />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
