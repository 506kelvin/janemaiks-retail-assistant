/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#e8f0fe',
          100: '#c5d9f8',
          200: '#9dbcf3',
          300: '#6a9aed',
          400: '#4a81e8',
          500: '#0047AB',
          600: '#003d96',
          700: '#00307a',
          800: '#002461',
          900: '#001a45',
        },
        secondary: {
          50: '#e8f5e9',
          100: '#c8e6c9',
          200: '#a5d6a7',
          300: '#66bb6a',
          400: '#43a047',
          500: '#2E8B57',
          600: '#257347',
          700: '#1b5e39',
          800: '#134b2d',
          900: '#0d3721',
        },
        accent: {
          50: '#fff3e0',
          100: '#ffe0b2',
          200: '#ffcc80',
          300: '#ffb74d',
          400: '#ffa726',
          500: '#FF6F00',
          600: '#e65f00',
          700: '#cc5200',
          800: '#b34400',
          900: '#993800',
        },
        status: {
          low: '#D32F2F',
          warning: '#FBC02D',
          success: '#388E3C',
        },
        dark: {
          bg: '#121212',
          card: '#1E1E1E',
          surface: '#222222',
          border: '#2A2A2A',
          text: '#F5F5F5',
          muted: '#9E9E9E',
        },
      },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'card-hover': '0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -2px rgba(0,0,0,0.04)',
        'elevated': '0 20px 25px -5px rgba(0,0,0,0.08), 0 10px 10px -5px rgba(0,0,0,0.04)',
        'glass': '0 8px 32px rgba(0,0,0,0.06)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'counter': 'counter 0.6s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'bounce-slow': 'bounce 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
};
