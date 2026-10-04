"use client";
import Link from 'next/link';
import { Sparkles, ArrowRight } from 'lucide-react';

interface FragranceCardProps {
  id?: string;
  brand: string;
  name: string;
  price: string;
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
  gender?: string;
  storeCount?: number;
}

export default function FragranceCard({
  id,
  brand,
  name,
  price,
  concentration = "EDP",
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
  gender,
  storeCount,
}: FragranceCardProps) {
  const isDupeActive = Boolean(isDupe ?? is_dupe);
  const targetName = inspiredBy || inspired_by || target || "Target";
  const displayImage = imageUrl || image_url;
  const displaySegment = marketSegment || market_segment;

  const genderLower = gender?.toLowerCase();
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

  const cardContent = (
    <div className="glass glass-hover rounded-2xl p-4 flex flex-col relative overflow-hidden group cursor-pointer h-full border border-white/10 hover:border-gold/30 transition-all duration-300">
      {/* Bottle Image Container */}
      <div className="w-full h-48 rounded-xl overflow-hidden bg-black/40 border border-white/5 mb-4 relative flex items-center justify-center group-hover:border-gold/20 transition-all">
        {displayImage ? (
          <img 
            src={displayImage} 
            alt={name} 
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={(e) => {
              (e.target as HTMLElement).style.display = 'none';
            }}
          />
        ) : (
          <div className="flex flex-col items-center justify-center text-white/30 gap-2">
            <Sparkles size={28} className="text-gold/40" />
            <span className="text-xs uppercase tracking-wider font-semibold">{brand}</span>
          </div>
        )}
        
        {/* Badges Container */}
        <div className="absolute top-2 left-2 flex flex-wrap gap-1.5 items-center z-10 max-w-[70%]">
          {displaySegment && (
            <div className="bg-black/75 backdrop-blur-md border border-white/10 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase text-gold shadow-sm">
              {displaySegment.replace(/_/g, ' ')}
            </div>
          )}
          {genderLabel && (
            <div className={`backdrop-blur-md border px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase shadow-sm ${genderClass}`}>
              {genderLabel}
            </div>
          )}
        </div>
        
        {/* Dupe Badge */}
        {isDupeActive && (
          <div className="absolute top-2 right-2 bg-amber-500/20 backdrop-blur-md border border-amber-500/30 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase text-amber-300 flex items-center gap-1 z-10">
            <Sparkles size={10} className="text-amber-400" />
            <span>Dupe / Clone</span>
          </div>
        )}
      </div>

      <div className="flex-1 flex flex-col justify-between">
        <div>
          <div className="flex justify-between items-start mb-1">
            <span className="text-xs font-bold tracking-wider text-gold uppercase truncate max-w-[80%]">
              {brand}
            </span>
            {storeCount !== undefined && storeCount > 0 && (
              <span className="text-[10px] text-white/40 bg-white/5 px-2 py-0.5 rounded-full">
                {storeCount} {storeCount === 1 ? 'store' : 'stores'}
              </span>
            )}
          </div>
          
          <h3 className="text-base font-bold text-white group-hover:text-gold transition-colors line-clamp-1 mb-1">
            {name}
          </h3>
        </div>

        <div className="mt-4 pt-3 border-t border-white/10 flex flex-col">
          <div className="flex justify-between items-start mb-1">
            <div className="flex flex-col min-w-0 pr-2">
              <p className="text-[10px] text-white/40 uppercase tracking-wider mb-0.5">Lowest Price</p>
              <p className="text-lg font-black text-white">{price}</p>
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
      </div>
    </div>
  );

  if (id) {
    return <Link href={`/fragrance/${id}`} className="block h-full">{cardContent}</Link>;
  }

  return cardContent;
}
