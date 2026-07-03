/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 暗色主题色板
        'surface': {
          'base': '#0f0f11',
          'raised': '#1a1a1e',
          'overlay': '#242429',
          'elevated': '#2a2a30',
        },
        'border': {
          DEFAULT: '#333338',
          'light': '#2a2a30',
          'focus': '#3b82f6',
        },
        'text': {
          'primary': '#e8e8ed',
          'secondary': '#a0a0a8',
          'tertiary': '#6b6b75',
          'disabled': '#4a4a55',
        },
        'accent': {
          DEFAULT: '#3b82f6',
          'hover': '#2563eb',
          'muted': 'rgba(59,130,246,0.15)',
        },
        'status': {
          'success': '#22c55e',
          'warning': '#f59e0b',
          'danger': '#ef4444',
          'info': '#06b6d4',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '0.875rem' }],
      },
      spacing: {
        '4.5': '1.125rem',
        '18': '4.5rem',
        '84': '21rem',
        '88': '22rem',
      },
      borderRadius: {
        'sm': '4px',
        'md': '8px',
        'lg': '12px',
        'xl': '16px',
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.3)',
        'elevated': '0 4px 12px rgba(0,0,0,0.4)',
        'dialog': '0 8px 32px rgba(0,0,0,0.5)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },
    },
  },
  plugins: [],
  // 避免与 Element Plus 冲突
  corePlugins: {
    preflight: false,
  },
}
