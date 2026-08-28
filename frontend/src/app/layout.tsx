import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    template: "%s | Fragrance Finder",
    default: "Fragrance Finder - Discover & Track the Best Perfumes",
  },
  description: "Discover the global fragrance market. Track prices, find your signature scent, explore sustainable perfume ingredients, and uncover the best organic fragrance blends for perfumes.",
  keywords: [
    "fragrance finder",
    "best organic fragrance blends for perfumes",
    "DIY customized perfume oils",
    "sustainable perfume ingredients for natural scents",
    "perfume raw materials marketplace for unique blends",
    "crafting personalized fragrance blends",
    "best-selling perfume oils",
    "scent combinations for bespoke perfumes",
    "how to create your own signature scent"
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased min-h-screen flex flex-col`}>
        <header className="sticky top-0 z-50 glass border-b-0 rounded-none bg-background/60">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="text-xl font-bold tracking-tighter">
                FRAGRANCE<span className="text-gradient-gold">FINDER</span>
              </span>
            </Link>
            
            <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-white/70">
              <Link href="/trending" className="hover:text-white transition-colors">Trending</Link>
              <Link href="/brands" className="hover:text-white transition-colors">Brands</Link>
              <Link href="/alerts" className="hover:text-white transition-colors">Alerts</Link>
            </nav>

            <div className="flex items-center gap-4">
              <button className="text-sm font-medium hover:text-white/80 transition-colors">
                Log in
              </button>
              <button className="text-sm font-medium bg-white text-black px-4 py-2 rounded-full hover:bg-white/90 transition-colors">
                Sign up
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-12">
          {children}
        </main>
      </body>
    </html>
  );
}
