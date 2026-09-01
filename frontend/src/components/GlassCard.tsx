'use client';

import { motion } from 'framer-motion';
import { ReactNode } from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export interface GlassCardProps {
  children?: ReactNode;
  className?: string;
  onClick?: () => void;
  hoverEffect?: boolean;
  delay?: number;
  id?: string;
  brand?: string;
  brand_name?: string;
  name?: string;
  canonical_name?: string;
  price?: string | number;
  concentration?: string;
  cloneConfidence?: number;
  isDupe?: boolean;
  is_dupe?: boolean;
  inspiredBy?: string;
  inspired_by?: string;
  target?: string;
  imageUrl?: string;
  image_url?: string;
  marketSegment?: string;
  market_segment?: string;
  storeCount?: number;
  store_count?: number;
}

export default function GlassCard({ 
  children, 
  className = '', 
  onClick, 
  hoverEffect = false,
  delay = 0,
  id,
  brand,
  brand_name,
  name,
  canonical_name,
  price,
  concentration = 'EDP',
  cloneConfidence,
  isDupe,
  is_dupe,
  inspiredBy,
  inspired_by,
  target,
  imageUrl,
  image_url,
  marketSegment,
  market_segment,
  storeCount,
  store_count,
}: GlassCardProps) {
  const baseClasses = hoverEffect ? 'glass glass-hover' : 'glass';
  const isDupeActive = Boolean(isDupe ?? is_dupe);
  const targetName = inspiredBy || inspired_by || target || 'Target';
  const displayBrand = brand || brand_name;
  const displayName = name || canonical_name;
  const displayImage = imageUrl || image_url;
  const displaySegment = marketSegment || market_segment;
  const displayStoreCount = storeCount ?? store_count;
  const formattedPrice = typeof price === 'number' ? `$${price.toFixed(2)}` : price;

  if (children) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay }}
        className={`rounded-xl overflow-hidden ${baseClasses} ${className}`}
        onClick={onClick}
        style={{ cursor: onClick ? 'pointer' : 'default' }}
      >
        {children}
        {price !== undefined && isDupeActive && (
          <div className="mt-3 pt-2 border-t border-white/10 flex flex-col">
            <span className="text-[10px] text-white/40 uppercase tracking-wider block mb-0.5">Price</span>
            <span className="text-lg font-black text-white block">{formattedPrice}</span>
            <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/15 border border-amber-500/30 text-[11px] font-medium text-amber-300 shadow-sm backdrop-blur-sm w-fit max-w-full">
              <Sparkles size={11} className="text-amber-400 shrink-0" />
              <span className="truncate">
                Inspired by: <strong className="text-white font-semibold">{targetName}</strong>
              </span>
            </div>
          </div>
        )}
      </motion.div>
    );
  }

  const cardBody = (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className={`rounded-2xl p-4 flex flex-col relative overflow-hidden group cursor-pointer h-full border border-white/10 hover:border-gold/30 transition-all duration-300 ${baseClasses} ${className}`}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      {/* Bottle Image Container */}
      <div className="w-full h-48 rounded-xl overflow-hidden bg-black/40 border border-white/5 mb-4 relative flex items-center justify-center group-hover:border-gold/20 transition-all">
        {displayImage ? (
          <img 
            src={displayImage} 
            alt={displayName || displayBrand || "Fragrance"} 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-white/30 gap-2">
            <Sparkles size={28} className="text-gold/40" />
            {displayBrand && (
              <span className="text-xs uppercase tracking-wider font-semibold">{displayBrand}</span>
            )}
          </div>
        )}

        {displaySegment && (
          <div className="absolute top-2 left-2 bg-black/70 backdrop-blur-md border border-white/10 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase text-gold">
            {displaySegment}
          </div>
        )}

        {isDupeActive && (
          <div className="absolute top-2 right-2 bg-amber-500/20 backdrop-blur-md border border-amber-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase text-amber-300 flex items-center gap-1">
            <Sparkles size={10} className="text-amber-400" />
            <span>Dupe / Clone</span>
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col justify-between">
        <div>
          {displayBrand && (
            <div className="flex justify-between items-start mb-1">
              <span className="text-xs font-bold tracking-wider text-gold uppercase truncate max-w-[80%]">
                {displayBrand}
              </span>
              {displayStoreCount !== undefined && displayStoreCount > 0 && (
                <span className="text-[10px] text-white/40 bg-white/5 px-2 py-0.5 rounded-full">
                  {displayStoreCount} {displayStoreCount === 1 ? 'store' : 'stores'}
                </span>
              )}
            </div>
          )}

          {displayName && (
            <h3 className="text-base font-bold text-white group-hover:text-gold transition-colors line-clamp-1 mb-1">
              {displayName}
            </h3>
          )}
        </div>

        {price !== undefined && (
          <div className="mt-4 pt-3 border-t border-white/10 flex flex-col">
            <div className="flex justify-between items-start mb-1">
              <div className="flex flex-col min-w-0 pr-2">
                <p className="text-[10px] text-white/40 uppercase tracking-wider mb-0.5">Lowest Price</p>
                <p className="text-lg font-black text-white">{formattedPrice}</p>
                {isDupeActive && (
                  <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/15 border border-amber-500/30 text-[11px] font-medium text-amber-300 shadow-sm backdrop-blur-sm max-w-full">
                    <Sparkles size={11} className="text-amber-400 shrink-0" />
                    <span className="truncate">
                      Inspired by: <strong className="text-white font-semibold">{targetName}</strong>
                    </span>
                  </div>
                )}
              </div>

              <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center group-hover:bg-gold group-hover:text-black transition-colors shrink-0 mt-1">
                <ArrowRight size={14} />
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );

  if (id) {
    return <Link href={`/fragrance/${id}`} className="block h-full">{cardBody}</Link>;
  }

  return cardBody;
}

