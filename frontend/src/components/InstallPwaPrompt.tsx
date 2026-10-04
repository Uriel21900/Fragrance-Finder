"use client";

import { useState, useEffect } from "react";
import { Download, Smartphone, Share2, PlusSquare, X, Sparkles } from "lucide-react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export default function InstallPwaPrompt() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const [showIOSModal, setShowIOSModal] = useState(false);

  useEffect(() => {
    // 1. Check if already installed / running in standalone app mode
    const standaloneMedia = window.matchMedia("(display-mode: standalone)").matches;
    const isIOSStandalone = (window.navigator as unknown as { standalone?: boolean }).standalone === true;
    if (standaloneMedia || isIOSStandalone) {
      setIsStandalone(true);
      return;
    }

    // 2. Detect iOS
    const userAgent = window.navigator.userAgent.toLowerCase();
    const isAppleDevice = /iphone|ipad|ipod/.test(userAgent) || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
    setIsIOS(isAppleDevice);

    // 3. Listen for Android/Chrome beforeinstallprompt event
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      // Only show if user hasn't dismissed in the last 3 days
      const lastDismissed = localStorage.getItem("ff_pwa_dismissed");
      if (!lastDismissed || Date.now() - parseInt(lastDismissed, 10) > 3 * 24 * 60 * 60 * 1000) {
        setShowPrompt(true);
      }
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstall);

    // On iOS, if not standalone and not dismissed, show prompt after a brief moment
    if (isAppleDevice) {
      const lastDismissed = localStorage.getItem("ff_pwa_dismissed");
      if (!lastDismissed || Date.now() - parseInt(lastDismissed, 10) > 3 * 24 * 60 * 60 * 1000) {
        const timer = setTimeout(() => setShowPrompt(true), 2500);
        return () => clearTimeout(timer);
      }
    }

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstall);
    };
  }, []);

  const handleInstallClick = async () => {
    if (isIOS) {
      setShowIOSModal(true);
    } else if (deferredPrompt) {
      await deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice.outcome === "accepted") {
        setShowPrompt(false);
      }
      setDeferredPrompt(null);
    } else {
      // Fallback for browsers that don't emit prompt or desktop
      setShowIOSModal(true);
    }
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem("ff_pwa_dismissed", Date.now().toString());
  };

  if (isStandalone || !showPrompt) {
    return null;
  }

  return (
    <>
      {/* Floating PWA Install Banner */}
      <aside 
        aria-label="Install Fragrance Finder App"
        className="fixed bottom-4 left-4 right-4 md:left-auto md:right-6 md:w-[380px] z-50 animate-in fade-in slide-in-from-bottom-5 duration-500"
      >
        <div className="glass border border-gold/30 rounded-2xl p-4 shadow-[0_20px_50px_rgba(0,0,0,0.8)] backdrop-blur-xl relative overflow-hidden bg-gradient-to-br from-black/90 via-black/80 to-[#121008]/90">
          <div className="absolute top-0 right-0 p-2">
            <button
              onClick={handleDismiss}
              className="text-white/40 hover:text-white transition-colors p-1 rounded-full hover:bg-white/10"
              aria-label="Dismiss install banner"
            >
              <X size={16} />
            </button>
          </div>

          <div className="flex items-start gap-3.5 pr-6">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gold via-amber-600 to-amber-900 p-0.5 shrink-0 shadow-lg shadow-gold/20 flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/icon-192.png"
                alt="Fragrance Finder Logo"
                className="w-full h-full object-cover rounded-[10px]"
              />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5 mb-0.5">
                <h4 className="text-sm font-bold text-white tracking-tight">Fragrance Finder App</h4>
                <span className="text-[10px] uppercase font-bold text-gold bg-gold/15 px-1.5 py-0.5 rounded border border-gold/30">
                  Mobile
                </span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed line-clamp-2">
                {isIOS 
                  ? "Install to your iPhone home screen for instant fullscreen access & price tracking." 
                  : "Install on your Android device for instant 1-tap price alerts and zero app store delays."}
              </p>
            </div>
          </div>

          <div className="mt-3.5 pt-3 border-t border-white/10 flex items-center justify-between gap-3">
            <button
              onClick={handleDismiss}
              className="text-xs font-semibold text-white/50 hover:text-white transition-colors px-2 py-1.5"
            >
              Not Now
            </button>
            <button
              onClick={handleInstallClick}
              className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-gold to-amber-500 hover:from-amber-400 hover:to-gold text-black font-bold text-xs px-4 py-2 rounded-xl transition-all shadow-md shadow-gold/20 hover:scale-[1.02] active:scale-[0.98]"
            >
              <Download size={14} className="stroke-[2.5]" />
              <span>{isIOS ? "Add to iPhone" : "Install App"}</span>
            </button>
          </div>
        </div>
      </aside>

      {/* iOS Installation Instructions Modal */}
      {showIOSModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="relative w-full max-w-md rounded-3xl glass border border-gold/30 p-6 shadow-2xl bg-gradient-to-b from-[#16161c] to-[#0a0a0e] text-white">
            <button
              onClick={() => setShowIOSModal(false)}
              className="absolute top-4 right-4 text-white/40 hover:text-white p-1 rounded-full hover:bg-white/10"
              aria-label="Close modal"
            >
              <X size={20} />
            </button>

            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gold/20 border border-gold/40 flex items-center justify-center text-gold">
                <Smartphone size={22} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Install on iPhone / iPad</h3>
                <p className="text-xs text-white/50">Follow these 2 simple steps in Safari</p>
              </div>
            </div>

            <div className="space-y-4 my-6 text-sm text-white/80">
              <div className="flex items-start gap-3 bg-white/5 p-3.5 rounded-2xl border border-white/10">
                <div className="w-7 h-7 rounded-full bg-sky-500/20 text-sky-400 border border-sky-500/30 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                  1
                </div>
                <div className="flex-1">
                  <p className="leading-snug">
                    Tap the <strong className="text-white font-semibold">Share</strong> button at the bottom of Safari.
                  </p>
                  <div className="inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded-md bg-white/10 text-xs text-white font-medium border border-white/15">
                    <Share2 size={13} className="text-sky-400" />
                    <span>Share Icon</span>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 bg-white/5 p-3.5 rounded-2xl border border-white/10">
                <div className="w-7 h-7 rounded-full bg-gold/20 text-gold border border-gold/30 flex items-center justify-center shrink-0 font-bold text-xs mt-0.5">
                  2
                </div>
                <div className="flex-1">
                  <p className="leading-snug">
                    Scroll down and tap <strong className="text-gold font-semibold">&ldquo;Add to Home Screen&rdquo;</strong>, then tap <strong className="text-white font-semibold">Add</strong>.
                  </p>
                  <div className="inline-flex items-center gap-1.5 mt-2 px-2.5 py-1 rounded-md bg-gold/15 text-xs text-gold font-medium border border-gold/30">
                    <PlusSquare size={13} className="text-gold" />
                    <span>Add to Home Screen</span>
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowIOSModal(false)}
              className="w-full py-3 bg-white/10 hover:bg-white/15 border border-white/20 rounded-xl text-sm font-semibold transition-colors text-white"
            >
              Got It
            </button>
          </div>
        </div>
      )}
    </>
  );
}
