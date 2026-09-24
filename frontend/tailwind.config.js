/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        factory: {
          bg: '#f4f5f8',
          sidebar: '#ffffff',
          card: '#ffffff',
          border: '#e2e8f0',
          borderLight: '#f1f5f9',
          navy: '#0f172a',
          navyHover: '#1e293b',
          muted: '#64748b',
          lightMuted: '#94a3b8',
          accent: '#2563eb',
          emerald: '#059669',
          emeraldBg: '#ecfdf5',
          amber: '#d97706',
          amberBg: '#fffbeb',
          rose: '#e11d48',
          roseBg: '#fff1f2',
          indigo: '#4f46e5',
          indigoBg: '#eeedff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgb(0 0 0 / 0.05), 0 1px 2px -1px rgb(0 0 0 / 0.05)',
        'nav': '0 4px 12px -2px rgb(15 23 42 / 0.12)',
      },
    },
  },
  plugins: [],
}
