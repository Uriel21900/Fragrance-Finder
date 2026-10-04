"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Flame, Tag, Bell } from "lucide-react";

export default function BottomMobileNav() {
  const pathname = usePathname();

  const navItems = [
    { label: "Home", href: "/", icon: Home },
    { label: "Trending", href: "/trending", icon: Flame },
    { label: "Brands", href: "/brands", icon: Tag },
    { label: "Alerts", href: "/alerts", icon: Bell },
  ];

  return (
    <nav 
      aria-label="Mobile Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-black/85 backdrop-blur-xl border-t border-white/10 px-4 py-2 pb-[max(0.5rem,env(safe-area-inset-bottom))]"
    >
      <div className="flex items-center justify-around">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition-all ${
                isActive
                  ? "text-gold font-bold scale-105"
                  : "text-white/50 hover:text-white/80 font-medium"
              }`}
            >
              <Icon size={20} className={isActive ? "text-gold" : "text-white/60"} />
              <span className="text-[10px] tracking-tight">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
