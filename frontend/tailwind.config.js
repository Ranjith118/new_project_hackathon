/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'industrial': {
          'bg': '#0F1419',
          'bg-secondary': '#1A2332',
          'card': '#1E293B',
          'border': '#334155',
          'text': '#F1F5F9',
          'text-muted': '#94A3B8',
          'accent': '#F97316',
          'success': '#10B981',
          'warning': '#FBBF24',
          'danger': '#EF4444',
        }
      },
      fontFamily: {
        'heading': ['Oxanium', 'sans-serif'],
        'body': ['IBM Plex Sans', 'sans-serif'],
        'mono': ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow': '0 0 20px rgba(249, 115, 22, 0.3)',
        'inset-dark': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.4)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(249, 115, 22, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(249, 115, 22, 0.4)' },
        }
      }
    },
  },
  plugins: [],
}