import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        obsidian: {
          DEFAULT: '#0a0a0a',
          lighter: '#1a1a1a',
          glass: 'rgba(20, 20, 20, 0.65)'
        },
        gold: {
          DEFAULT: '#d4af37',
          muted: '#a88a2a',
          light: '#f3e5ab'
        },
        glass: {
          border: 'rgba(255, 255, 255, 0.08)',
          highlight: 'rgba(255, 255, 255, 0.05)'
        }
      },
      backgroundImage: {
        'luxury-gradient': 'radial-gradient(circle at top right, #1a1a1a, #050505)',
      },
      animation: {
        'glow': 'glow 3s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 10px rgba(212, 175, 55, 0.1)' },
          '100%': { boxShadow: '0 0 20px rgba(212, 175, 55, 0.3)' },
        }
      }
    },
  },
  plugins: [],
};
export default config;
