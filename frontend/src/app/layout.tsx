import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import InstallPwaPrompt from "@/components/InstallPwaPrompt";
import BottomMobileNav from "@/components/BottomMobileNav";
import ServiceWorkerRegister from "@/components/ServiceWorkerRegister";

const inter = Inter({ subsets: ["latin"] });

export const viewport: Viewport = {
  themeColor: "#08080a",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  title: {
    template: "%s | Fragrance Finder",
    default: "Fragrance Finder — Luxury & Clone Price Tracker",
  },
  description: "Discover the global fragrance market. Track prices, find your signature scent, explore sustainable perfume ingredients, and uncover the best organic fragrance blends for perfumes.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Fragrance Finder",
  },
  icons: {
    icon: [
      { url: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
  },
  keywords: [
    "fragrance finder",
    "perfume price tracker",
    "best clone fragrances",
    "cologne discounter comparison",
    "creed aventus clones",
    "baccarat rouge 540 dupes",
    "niche perfumes",
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
        <ServiceWorkerRegister />
        
        <header className="sticky top-0 z-50 glass border-b-0 rounded-none bg-background/60">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
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

            <div className="flex items-center gap-3">
              <button className="text-sm font-medium hover:text-white/80 transition-colors">
                Log in
              </button>
              <button className="text-sm font-medium bg-white text-black px-4 py-2 rounded-full hover:bg-white/90 transition-colors">
                Sign up
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-12 pb-24 md:pb-12">
          {children}
        </main>

        <BottomMobileNav />
        <InstallPwaPrompt />
      </body>
    </html>
  );
}
