'use client';

import { useState, useEffect } from "react";
import axios from "axios";
import { DealData } from "@/types";

import FragranceCard from "@/components/FragranceCard";

export default function AlertsPage() {
  const [deals, setDeals] = useState<DealData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDeals() {
      try {
        const res = await axios.get("http://localhost:8000/api/alerts/deals");
        setDeals(res.data);
      } catch (err) {
        console.error("Failed to fetch deals", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDeals();
  }, []);

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Price Drop Alerts</h1>
          <p className="text-white/60">
            Live feed of the latest fragrance deals discovered by our scrapers.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse space-y-4">
          <div className="h-40 bg-white/5 rounded-xl"></div>
          <div className="h-40 bg-white/5 rounded-xl"></div>
          <div className="h-40 bg-white/5 rounded-xl"></div>
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {deals.length === 0 ? (
            <div className="text-center py-20 text-white/50">
              No recent price drops found. Check back later!
            </div>
          ) : (
            deals.map((deal, idx) => (
              <div key={idx} className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col md:flex-row items-center gap-6 hover:border-orange-500/50 transition-colors">
                <div className="w-full md:w-1/4">
                  <FragranceCard 
                    id={deal.fragrance.dna_id}
                    brand={deal.fragrance.brand_name}
                    name={deal.fragrance.canonical_name}
                    price={`$${deal.sale_price.toFixed(2)}`}
                    concentration="EDP"
                    isDupe={deal.fragrance.is_dupe}
                    inspiredBy={deal.fragrance.inspired_by}
                  />
                </div>
                
                <div className="flex-1 flex flex-col items-center md:items-start text-center md:text-left space-y-4">
                  <h3 className="text-2xl font-bold">{deal.fragrance.brand_name}</h3>
                  <h4 className="text-xl text-white/80">{deal.fragrance.canonical_name}</h4>
                  
                  <div className="flex flex-wrap items-center gap-4 mt-4">
                    <span className="text-sm font-semibold bg-white/10 px-3 py-1 rounded-full">
                      Found at {deal.retailer_name}
                    </span>
                    <span className="text-sm text-red-400 line-through">
                      ${deal.original_price.toFixed(2)}
                    </span>
                    <span className="text-3xl font-bold text-green-400">
                      ${deal.sale_price.toFixed(2)}
                    </span>
                  </div>
                  
                  <a 
                    href={deal.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 px-8 py-3 bg-white text-black font-semibold rounded-xl hover:bg-gray-200 transition-colors w-full md:w-auto text-center"
                  >
                    View Deal
                  </a>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
