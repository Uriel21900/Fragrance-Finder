import SearchBar from "@/components/SearchBar";
import TrendingSection from "@/components/TrendingSection";

export default function Home() {
  return (
    <div className="w-full flex flex-col items-center pt-20 pb-32">
      {/* Hero Section */}
      <section className="w-full max-w-4xl text-center flex flex-col items-center mb-16">
        <h1 className="text-5xl md:text-7xl font-black tracking-tighter mb-6 text-balance">
          Discover the Global{" "}
          <span className="text-gradient-gold">Fragrance Market</span>
        </h1>
        <p className="text-lg md:text-xl text-white/60 mb-12 max-w-2xl text-balance">
          Track real-time prices for over 150,000 fragrances. Find the perfect clone, explore sustainable perfume ingredients, discover the best organic fragrance blends, and never overpay for your signature scent again.
        </p>
        
        <SearchBar />
        
        <div className="mt-8 flex flex-wrap justify-center items-center gap-2.5 text-sm">
          <span className="text-white/40 text-xs uppercase tracking-wider font-semibold mr-1">Popular:</span>
          <a href="/search?q=Baccarat+Rouge+540" className="px-3 py-1 bg-white/5 hover:bg-gold/20 hover:border-gold/40 border border-white/10 rounded-full text-white/80 hover:text-white transition-all text-xs font-medium">Baccarat Rouge 540</a>
          <a href="/search?q=Aventus" className="px-3 py-1 bg-white/5 hover:bg-gold/20 hover:border-gold/40 border border-white/10 rounded-full text-white/80 hover:text-white transition-all text-xs font-medium">Creed Aventus</a>
          <a href="/search?q=Layton" className="px-3 py-1 bg-white/5 hover:bg-gold/20 hover:border-gold/40 border border-white/10 rounded-full text-white/80 hover:text-white transition-all text-xs font-medium">PDM Layton</a>
          <a href="/search?q=Angels+Share" className="px-3 py-1 bg-white/5 hover:bg-gold/20 hover:border-gold/40 border border-white/10 rounded-full text-white/80 hover:text-white transition-all text-xs font-medium">Angels&apos; Share</a>
          <a href="/search?q=Tobacco+Vanille" className="px-3 py-1 bg-white/5 hover:bg-gold/20 hover:border-gold/40 border border-white/10 rounded-full text-white/80 hover:text-white transition-all text-xs font-medium">Tobacco Vanille</a>
          <a href="/search?q=Detour+Noir" className="px-3 py-1 bg-white/5 hover:bg-gold/20 hover:border-gold/40 border border-white/10 rounded-full text-white/80 hover:text-white transition-all text-xs font-medium">Detour Noir</a>
        </div>
      </section>

      {/* Trending Section */}
      <TrendingSection />
    </div>
  );
}
