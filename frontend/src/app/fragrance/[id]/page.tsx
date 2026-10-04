/* eslint-disable @next/next/no-img-element */
'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { ArrowLeft, ExternalLink, Activity, Info, Bell, Copy, Sparkles, ShoppingBag, ShieldCheck, Tag } from 'lucide-react';
import Link from 'next/link';
import GlassCard from '@/components/GlassCard';
import { FragranceData, Price, Clone } from '@/types';

export default function FragranceDetail({ params }: { params: { id: string } }) {
  const [fragrance, setFragrance] = useState<FragranceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [alertEmail, setAlertEmail] = useState('');
  const [alertPrice, setAlertPrice] = useState('');
  const [alertStatus, setAlertStatus] = useState<string | null>(null);
  const [imgSrc, setImgSrc] = useState<string>('');

  const handleSetAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('/api/alerts/subscribe', {
        email: alertEmail,
        dna_id: params.id,
        target_price: parseFloat(alertPrice)
      });
      setAlertStatus("Alert created successfully!");
      setTimeout(() => { setShowModal(false); setAlertStatus(null); setAlertEmail(''); setAlertPrice(''); }, 2000);
    } catch (err) {
      console.error(err);
      setAlertStatus("Failed to set alert. Please try again.");
    }
  };

  useEffect(() => {
    async function fetchDetail() {
      try {
        const res = await axios.get(`/api/fragrance/${params.id}`);
        setFragrance(res.data);
        if (res.data.image_url) {
          setImgSrc(res.data.image_url);
        } else {
          setImgSrc('');
        }
      } catch (err) {
        console.error("Error fetching fragrance details:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchDetail();
  }, [params.id]);

  if (loading) {
    return (
      <div className="w-full mt-32 text-center flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 border-2 border-gold/20 border-t-gold rounded-full animate-spin"></div>
        <p className="text-white/50 text-sm">Loading market prices &amp; fragrance data...</p>
      </div>
    );
  }

  if (!fragrance) {
    return (
      <div className="w-full mt-24 text-center text-white/50">
        <p className="text-xl mb-4">Fragrance not found.</p>
        <Link href="/" className="inline-flex items-center gap-2 text-gold hover:underline">
          <ArrowLeft size={16} /> Back to Search
        </Link>
      </div>
    );
  }

  // Helper to extract clean website domain (e.g. reblscents.com, perfumeonline.com, banadirfragrance.com)
  const getWebsiteDomain = (price: ComparablePrice): string => {
    try {
      if (price.source_url) {
        const url = new URL(price.source_url);
        let host = url.hostname.replace(/^www\./, '').toLowerCase();
        if (host === 'perfumeonline.ca') host = 'perfumeonline.com';
        if (host === 'labelleperfumes.com') host = 'labelle.com';
        return host;
      }
    } catch {}
    if (price.retailer_name && price.retailer_name !== 'Unknown') {
      let r = price.retailer_name.toLowerCase().replace(/\s+/g, '');
      if (!r.includes('.')) r += '.com';
      if (r === 'perfumeonline.ca') r = 'perfumeonline.com';
      if (r === 'labelleperfumes.com' || r.includes('labelle')) r = 'labelle.com';
      return r;
    }
    return 'Direct Retailer';
  };

  const getCleanProductUrl = (rawUrl: string): string => {
    try {
      const u = new URL(rawUrl);
      return `${u.origin}${u.pathname}`.toLowerCase();
    } catch {
      return rawUrl;
    }
  };

  // Extract and aggregate ALL unique product offers across variants
  type ComparablePrice = Price & { volume_ml?: number; package_type?: string };
  const allPrices: ComparablePrice[] = [];
  const seenProductKeys = new Map<string, ComparablePrice>();

  if (fragrance.variants) {
    for (const variant of fragrance.variants) {
      if (variant.prices) {
        for (const price of variant.prices) {
          const cleanUrl = getCleanProductUrl(price.source_url);
          const domain = getWebsiteDomain(price);
          // Key by domain + product URL path + size
          const key = `${domain}-${cleanUrl}-${variant.volume_ml}`;

          const existing = seenProductKeys.get(key);
          if (!existing || new Date(price.captured_at) > new Date(existing.captured_at)) {
            seenProductKeys.set(key, {
              ...price,
              volume_ml: price.volume_ml || variant.volume_ml,
              package_type: price.package_type || variant.package_type,
            });
          }
        }
      }
    }
  }

  Array.from(seenProductKeys.values()).forEach((price) => {
    allPrices.push(price);
  });

  // Sort prices ascending (lowest price first)
  allPrices.sort((a, b) => a.price_amount - b.price_amount);

  const lowestPrice = allPrices.length > 0 ? allPrices[0].price_amount : null;
  const highestPrice = allPrices.length > 0 ? allPrices[allPrices.length - 1].price_amount : null;

  const genderLower = fragrance.gender?.toLowerCase();
  let genderLabel = "";
  let genderClass = "";
  if (genderLower === 'masculine' || genderLower === 'men' || genderLower === 'him') {
    genderLabel = "Men";
    genderClass = "bg-sky-500/20 text-sky-300 border-sky-500/40";
  } else if (genderLower === 'feminine' || genderLower === 'women' || genderLower === 'her') {
    genderLabel = "Women";
    genderClass = "bg-rose-500/20 text-rose-300 border-rose-500/40";
  } else if (genderLower === 'unisex') {
    genderLabel = "Unisex";
    genderClass = "bg-purple-500/20 text-purple-300 border-purple-500/40";
  }

  return (
    <div className="w-full pb-32">
      {/* Back button */}
      <Link href="/" className="inline-flex items-center gap-2 text-white/50 hover:text-white mb-8 transition-colors">
        <ArrowLeft size={16} />
        <span className="text-sm font-medium">Back to Search</span>
      </Link>

      {/* Hero / Header with Fragrance Picture */}
      <div className="mb-12 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Fragrance Image Card */}
        <div className="lg:col-span-4 flex justify-center">
          <div className="relative group w-full max-w-sm rounded-3xl overflow-hidden glass border border-white/10 shadow-[0_15px_35px_rgba(0,0,0,0.6)]">
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent z-10"></div>
            
            {/* Ambient light glow */}
            <div className="absolute -inset-1 bg-gradient-to-r from-gold/20 via-amber-500/10 to-transparent rounded-3xl blur-xl opacity-50 group-hover:opacity-100 transition-opacity"></div>
            
            <div className="relative aspect-[4/5] w-full overflow-hidden bg-black/40 flex items-center justify-center">
              {imgSrc ? (
                <img
                  src={imgSrc}
                  alt={fragrance.canonical_name}
                  onError={() => setImgSrc('')}
                  className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-700 ease-out"
                />
              ) : (
                <div className="flex flex-col items-center justify-center text-white/30 gap-3 p-6 text-center">
                  <Sparkles size={48} className="text-gold/40" />
                  <span className="text-sm uppercase tracking-widest font-bold text-white/60">{fragrance.brand_name}</span>
                  <span className="text-xs text-white/40">{fragrance.canonical_name}</span>
                </div>
              )}
              
              {/* Overlay Tags */}
              <div className="absolute top-4 left-4 z-20 flex flex-col gap-2">
                <span className="px-3 py-1 bg-black/60 backdrop-blur-md border border-white/15 rounded-full text-xs font-semibold text-gold tracking-wide uppercase">
                  {fragrance.market_segment}
                </span>
                {genderLabel && (
                  <span className={`px-3 py-1 backdrop-blur-md border rounded-full text-xs font-semibold tracking-wide uppercase shadow-sm ${genderClass}`}>
                    {genderLabel}
                  </span>
                )}
                {fragrance.is_dupe && (
                  <span className="px-3 py-1 bg-amber-500/20 backdrop-blur-md border border-amber-500/40 rounded-full text-xs font-semibold text-amber-300">
                    Inspired Clone
                  </span>
                )}
              </div>

              {lowestPrice !== null && (
                <div className="absolute bottom-4 left-4 right-4 z-20 flex items-center justify-between bg-black/70 backdrop-blur-md border border-white/10 px-4 py-2.5 rounded-xl">
                  <span className="text-xs text-white/60">From</span>
                  <span className="text-xl font-extrabold text-gold">${lowestPrice.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Fragrance Info & Actions */}
        <div className="lg:col-span-8 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h2 className="text-gold font-bold tracking-[0.25em] uppercase text-sm">{fragrance.brand_name}</h2>
              <span className="text-white/20">•</span>
              <span className="flex items-center gap-1 text-xs text-green-400 font-medium">
                <Activity size={13} /> Actively Tracked
              </span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-white mb-4 tracking-tight">
              {fragrance.canonical_name}
            </h1>

            {fragrance.inspired_by && (
              <p className="text-sm font-medium text-amber-300/90 mb-4 flex items-center gap-1.5">
                <Sparkles size={16} className="text-amber-400" />
                Inspired by: <span className="text-white font-semibold">{fragrance.inspired_by}</span>
              </p>
            )}

            <div className="flex flex-wrap items-center gap-3 my-6">
              <div className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-sm text-white/70">
                <Tag size={15} className="text-gold" />
                <span>{allPrices.length} {allPrices.length === 1 ? 'Market Offer' : 'Market Offers'}</span>
              </div>
              {lowestPrice !== null && highestPrice !== null && (
                <div className="glass px-4 py-2 rounded-xl flex items-center gap-2 text-sm text-white/70">
                  <ShieldCheck size={15} className="text-green-400" />
                  <span>Price Range: <strong className="text-white">${lowestPrice.toFixed(2)}</strong> - <strong className="text-white">${highestPrice.toFixed(2)}</strong></span>
                </div>
              )}
              {genderLabel && (
                <div className={`glass px-4 py-2 rounded-xl text-sm font-medium border ${genderClass}`}>
                  Gender: <strong className="text-white">{genderLabel}</strong>
                </div>
              )}
              {fragrance.first_release_year && (
                <div className="glass px-4 py-2 rounded-xl text-sm text-white/70">
                  Released: <strong className="text-white">{fragrance.first_release_year}</strong>
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 pt-4 border-t border-white/10">
            <button 
              onClick={() => setShowModal(true)}
              className="flex items-center gap-2.5 px-6 py-3.5 bg-gold/10 hover:bg-gold/20 text-gold border border-gold/40 hover:border-gold/70 rounded-xl font-semibold transition-all shadow-[0_0_20px_rgba(212,175,55,0.15)]"
            >
              <Bell size={18} />
              <span>Set Price Alert</span>
            </button>
            {allPrices.length > 0 && (
              <a
                href={allPrices[0].source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-6 py-3.5 bg-white/10 hover:bg-white/20 text-white border border-white/15 rounded-xl font-medium transition-all"
              >
                <ShoppingBag size={18} />
                <span>Lowest Price: ${allPrices[0].price_amount.toFixed(2)} on {getWebsiteDomain(allPrices[0])}</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Pricing Comparison Grid */}
      <div className="mt-14">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-6">
          <div>
            <h3 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
              <ShoppingBag size={22} className="text-gold" /> Current Market Prices
            </h3>
            <p className="text-sm text-white/50">
              Live price comparison across all tracked websites and available sizes. Sorted from lowest to highest.
            </p>
          </div>
          <span className="text-xs text-white/40 uppercase tracking-wider font-semibold">
            {allPrices.length} Available {allPrices.length === 1 ? 'Site' : 'Sites'}
          </span>
        </div>
        
        {allPrices.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allPrices.map((price: ComparablePrice, idx: number) => {
              const website = getWebsiteDomain(price);
              const isBestPrice = idx === 0;

              return (
                <a 
                  href={price.source_url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  key={price.price_observation_id || `${price.source_url}-${idx}`}
                  className="block group"
                >
                  <GlassCard 
                    hoverEffect 
                    delay={idx * 0.04} 
                    className={`p-5 flex flex-col justify-between h-full relative overflow-hidden transition-all ${
                      isBestPrice 
                        ? 'border-gold/50 shadow-[0_0_25px_rgba(212,175,55,0.15)] bg-gold/[0.03]' 
                        : 'border-white/10 hover:border-white/25'
                    }`}
                  >
                    {isBestPrice && (
                      <div className="absolute top-0 right-0 bg-gold text-black text-[11px] font-black uppercase px-3 py-0.5 rounded-bl-lg tracking-wider shadow-sm">
                        Best Deal
                      </div>
                    )}

                    <div>
                      {/* Website Domain / Store Name */}
                      <div className="flex items-center justify-between mb-3 pr-16">
                        <span className="text-base font-bold text-white group-hover:text-gold transition-colors tracking-wide">
                          {website}
                        </span>
                      </div>

                      {/* Size & Bottle Type Badge */}
                      <div className="flex items-center gap-2 mb-4">
                        <span className="px-2.5 py-1 bg-white/5 border border-white/10 rounded-md text-xs font-medium text-white/80">
                          {price.volume_ml ? `${price.volume_ml} ml` : 'Standard Size'} • {price.package_type || 'spray'}
                        </span>
                      </div>
                    </div>

                    {/* Price and Visit Link */}
                    <div className="flex items-end justify-between pt-3 border-t border-white/5 mt-auto">
                      <div>
                        <span className="text-xs text-white/40 block mb-0.5">Price</span>
                        <span className={`text-2xl font-black ${isBestPrice ? 'text-gold' : 'text-white'} group-hover:text-gold transition-colors`}>
                          ${price.price_amount.toFixed(2)}
                        </span>
                      </div>

                      <div className="flex items-center gap-1.5 text-xs font-semibold text-white/70 group-hover:text-gold transition-colors bg-white/5 group-hover:bg-gold/10 px-3 py-2 rounded-lg border border-white/10 group-hover:border-gold/30">
                        <span>Visit Store</span>
                        <ExternalLink size={14} />
                      </div>
                    </div>
                  </GlassCard>
                </a>
              );
            })}
          </div>
        ) : (
          <GlassCard className="p-10 text-center text-white/50 flex flex-col items-center justify-center">
            <Info size={36} className="mb-4 text-white/20" />
            <p className="text-base text-white/70 font-medium mb-1">No active price observations found.</p>
            <p className="text-sm text-white/40">Our automated scrapers are scanning retailers to find new live offers.</p>
          </GlassCard>
        )}
      </div>

      {/* Clones Section */}
      {fragrance.clones && fragrance.clones.length > 0 && (
        <div className="mt-16">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
              <Copy size={22} className="text-gold" /> Known Clones / Inspired By
            </h3>
            <p className="text-sm text-white/50">
              Affordable impressions, dupes, and high-similarity alternatives.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {fragrance.clones.map((clone: Clone, idx: number) => (
              <Link href={`/fragrance/${clone.dna_id}`} key={clone.dna_id} className="block group">
                <GlassCard hoverEffect delay={idx * 0.05} className="p-4 flex items-center gap-4 border-white/10 hover:border-gold/30">
                  <div className="w-14 h-14 rounded-xl overflow-hidden bg-white/5 border border-white/10 shrink-0 flex items-center justify-center">
                    {clone.image_url ? (
                      <img 
                        src={clone.image_url} 
                        alt={clone.canonical_name} 
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                        onError={(e) => {
                          (e.target as HTMLElement).style.display = 'none';
                        }}
                      />
                    ) : (
                      <Sparkles size={20} className="text-gold/50" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-gold text-xs font-bold uppercase tracking-wider mb-0.5 truncate">{clone.brand_name}</h4>
                    <span className="text-base font-bold text-white group-hover:text-gold transition-colors block truncate">{clone.canonical_name}</span>
                  </div>
                  <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center shrink-0 group-hover:bg-gold group-hover:text-black transition-colors">
                    <ExternalLink size={14} />
                  </div>
                </GlassCard>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Alert Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <GlassCard className="max-w-md w-full p-8 relative border-gold/30 shadow-[0_0_50px_rgba(0,0,0,0.8)]">
            <button 
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-white/50 hover:text-white text-lg w-8 h-8 rounded-full flex items-center justify-center hover:bg-white/10 transition-colors"
            >
              ✕
            </button>
            <div className="flex items-center gap-2.5 mb-2">
              <Bell size={20} className="text-gold" />
              <h3 className="text-2xl font-bold text-white">Price Alert</h3>
            </div>
            <p className="text-white/60 text-sm mb-6">
              We&apos;ll notify you when <strong className="text-white">{fragrance.canonical_name}</strong> drops below your target price.
            </p>
            
            <form onSubmit={handleSetAlert} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">Email Address</label>
                <input 
                  type="email" 
                  required 
                  value={alertEmail}
                  onChange={e => setAlertEmail(e.target.value)}
                  className="w-full bg-black/50 border border-white/15 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold transition-all" 
                  placeholder="you@example.com" 
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-white/50 uppercase tracking-wider mb-2">Target Price ($)</label>
                <input 
                  type="number" 
                  step="0.01" 
                  required 
                  value={alertPrice}
                  onChange={e => setAlertPrice(e.target.value)}
                  className="w-full bg-black/50 border border-white/15 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-gold focus:ring-1 focus:ring-gold transition-all" 
                  placeholder={lowestPrice ? `e.g. ${(lowestPrice * 0.85).toFixed(2)}` : 'e.g. 150.00'}
                />
              </div>
              
              {alertStatus && (
                <div className={`text-sm p-3 rounded-lg ${alertStatus.includes("success") ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-red-500/10 text-red-400 border border-red-500/20"}`}>
                  {alertStatus}
                </div>
              )}
              
              <button 
                type="submit" 
                className="w-full mt-4 bg-gold hover:bg-gold/90 text-black font-bold py-3.5 rounded-xl transition-all shadow-[0_0_20px_rgba(212,175,55,0.2)]"
              >
                Create Price Alert
              </button>
            </form>
          </GlassCard>
        </div>
      )}
    </div>
  );
}
